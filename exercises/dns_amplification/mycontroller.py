#!/usr/bin/env python2
import argparse
import grpc
import os
import sys
from time import sleep
import signal
import json

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper
import runtime_CLI
import bmpy_utils as utils

from scapy.all import *
from scapy.contrib import lldp
from scapy.config import conf
from scapy.packet import bind_layers

# from concurrent import futures
# from p4.v1 import p4runtime_pb2
# from p4.v1 import p4runtime_pb2_grpc

import networkx as nx
import matplotlib.pyplot as plt


SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2

topology = {}
link_num = 0



def GePacketOut(egress_port, mcast, padding):
    out1 = "{0:09b}".format(egress_port)
    out2 = "{0:016b}".format(mcast)
    out3 = "{0:07b}".format(padding)
    out = out1+out2+out3
    a = bytearray([int(out[0:8],2),int(out[8:16],2),int(out[16:24],2),int(out[24:32],2)])
    return a

def ParsePacketIn(pin):
    srcAddr = ""
    dstAddr = ""

    for i in range(0,6):
        dstAddr = dstAddr + str("{0:02x}".format(int("{0:08b}".format(pin[i]),2)))
        if i != 5:
            dstAddr = dstAddr + ":"

    for i in range(6,12):
        srcAddr = srcAddr + str("{0:02x}".format(int("{0:08b}".format(pin[i]),2)))
        if i != 11:
            srcAddr = srcAddr + ":"

    pktIn = {}
    pktIn["srcAddr"] = srcAddr
    pktIn["dstAddr"] = dstAddr
    
    etype = ""
    for i in range(12,14):
        etype = etype + "{0:08b}".format(pin[i])
    pktIn["type"] = hex(int(etype,2))
    
    pkt = ""

    for i in range(16,19):
        pkt = pkt + "{0:08b}".format(pin[i])

    pktIn["sport"] = int(pkt[0:9],2)
    pktIn["dport"] = int(pkt[9:18],2)
    # pktIn["padding"] = int(pkt[18:24],2)

    return pktIn

def recordLink(p):
    link = {}
    link[p['srcAddr']] = p['sport']
    link[p['dstAddr']] = p['dport']
    flag = 0 # check if link already exist in topology
    for index, l in topology.items():
        if l == link:
            flag = 1
            break

    if flag == 0:
        global link_num
        topology[str(link_num)] = link
        link_num += 1
        
def sendPacketOut(p4info_helper, sw, port, mcast):
    packet = GePacketOut(port, mcast, 0) #padding must be 0
    packet_out = p4info_helper.buildPacketOut(payload = str(packet))
    # print packet_out
    sw.SendLLDP(packet_out)

def recvPacketIn(sw):
    try:
        content = sw.RecvLLDP()
        if content != None and content.WhichOneof('update')=='packet':
            packet = content.packet.payload
            # print content
            pkt = bytearray(packet)
            p = ParsePacketIn(pkt)
            # print p
            recordLink(p)
    except Exception, e:
        None

def writeIPRules(p4info_helper, ingress_sw, dst_eth_addr, dst_ip, mask, port):
    table_entry = p4info_helper.buildTableEntry(
        table_name = "MyIngress.ipv4_lpm",
        match_fields = {
            "hdr.ipv4.dstAddr": (dst_ip, mask)
        },
        action_name = "MyIngress.ipv4_forward",
        action_params={
            "dstAddr":dst_eth_addr,
            "port":port
        })
    ingress_sw.WriteTableEntry(table_entry)

def writeRecordRules(p4info_helper, ingress_sw, qr_code):
    table_entry = p4info_helper.buildTableEntry(
        table_name = "MyIngress.dns_response_record",
        match_fields = {
            "hdr.dns.qr": qr_code
        },
        action_name = "MyIngress.record_response"
        )
    ingress_sw.WriteTableEntry(table_entry)

def writeHash1Rule(p4info_helper, ingress_sw):
    table_entry = p4info_helper.buildTableEntry(
        table_name = "MyIngress.dns_request_hash_lpm",
        match_fields = {
            "hdr.dns.qr": 0
        },
        action_name = "MyIngress.dns_request_hash_1",
        )
    ingress_sw.WriteTableEntry(table_entry)

def writePInRule(p4info_helper, ingress_sw, etherType, sw_addr):
    table_entry = p4info_helper.buildTableEntry(
        table_name = "MyIngress.pkt_in_table",
        match_fields = {
            "hdr.ethernet.etherType": etherType
        },
        action_name = "MyIngress.send_to_cpu",
        action_params={
            "swAddr": sw_addr
        })
    ingress_sw.WriteTableEntry(table_entry)
    
def writePOutRule(p4info_helper, ingress_sw, padding, sw_addr):
    table_entry = p4info_helper.buildTableEntry(
        table_name = "MyIngress.pkt_out_table",
        match_fields = {
            "hdr.packet_out.padding": padding
        },
        action_name = "MyIngress.lldp_forward",
        action_params={
            "swAddr": sw_addr
        })
    ingress_sw.WriteTableEntry(table_entry)

def printGrpcError(e):
    print "gRPC Error:", e.details(),
    status_code = e.code()
    print "(%s)" % status_code.name,
    traceback = sys.exc_info()[2]
    print "[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno)

def printRegister(p4info_helper, sw, register_name, index):
    for response in sw.ReadRegisters(p4info_helper.get_registers_id(register_name), index, dry_run=False):
        for entity in response.entities:
            register = entity.register_entry
            print "%s %s %d: %s" % (sw.name, register_name, index, register.data.data.enum)

def printCounter(p4info_helper, sw, counter_name, index):
    for response in sw.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
        for entity in response.entities:
            counter = entity.counter_entry
            print "%s %s %d: %d" % (
                sw.name, counter_name, index, counter.data.packet_count
            )

def read_register(runtimeAPI, name, index):
    reg = runtimeAPI.get_res("register", name, 
                            runtime_CLI.ResType.register_array)
    return runtimeAPI.client.bm_register_read(0, reg.name, index)

def write_register(runtimeAPI, name, index, value):
    register = runtimeAPI.get_res("register", name, 
                            runtime_CLI.ResType.register_array)
    runtimeAPI.client.bm_register_write(0, register.name, index, value)

def connectThrift(port, bmv2_file_path):
    standard_client, mc_client = utils.thrift_connect(
        'localhost', port,
        runtime_CLI.RuntimeAPI.get_thrift_services(runtime_CLI.PreType.SimplePre)
    )

    runtime_CLI.load_json_config(standard_client, bmv2_file_path)
    return runtime_CLI.RuntimeAPI(runtime_CLI.PreType.SimplePre, standard_client, mc_client)

def draw_topology(sw_mac, hosts):
    G = nx.Graph()
    reverse = {}
    for s, mac in sw_mac.items():
        G.add_node(mac.encode('utf-8'))
        reverse[mac] = s

    for h, mac in hosts.items():
        G.add_node(mac.encode('utf-8'))
        reverse[mac] = h

    # print topology
    edge = []
    for link in topology.values():
        keys = link.keys()
        edge.append((keys[0],keys[1]))

    G.add_edges_from(edge)
    
    pos=nx.spring_layout(G)
    nx.draw_networkx_labels(G,pos,reverse,font_size=12)
    print pos
    nx.draw(G, pos = pos)
    plt.show()

def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)


    try:
        sw_mac = {}
        with open("switch.txt", "r") as f:
            for line in f:
                sw_mac[line.split()[0]] = line.split()[1]
        # Create a switch connection object for s1 s2 s3;
        # this is backed by a P4Runtime gRPC connection.
        # Also, dump all P4Runtime messages sent to switch to given txt files.
        sw = []
        for i in range(1,len(sw_mac)+1):
            s = p4runtime_lib.bmv2.Bmv2SwitchConnection(
                    name='s'+str(i),
                    address='127.0.0.1:'+str(50050+i),
                    device_id=i-1,
                    proto_dump_file='logs/s'+str(i)+'-p4runtime-requests.txt')
            # Send master arbitration update message to establish this controller as
            # master (required by P4Runtime before performing any other write operation)
            s.MasterArbitrationUpdate()

            # Install the P4 program on the switches
            s.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                    bmv2_json_file_path=bmv2_file_path)
            print "Installed P4 Program using SetForwardingPipelineConfig on s"+str(i)
            sw.append(s)


        #############################################################################
        
        
        

        hosts = {}
        with open("host.json", "r") as host_file:
            host_inf = json.load(host_file)
            for s, sw_inf in host_inf.items():
                for port, p_inf in sw_inf.items():
                    recordLink({"srcAddr":sw_mac[s], "sport":int(port),
                                 "dstAddr":p_inf["mac"], "dport":1})
                    hosts[p_inf["name"]] = p_inf["mac"]



        writeIPRules(p4info_helper, ingress_sw=sw[0], dst_eth_addr="00:00:00:00:01:01", dst_ip="10.0.1.1", mask=32, port=1)
        writeIPRules(p4info_helper, ingress_sw=sw[0], dst_eth_addr="00:00:00:03:03:00", dst_ip="10.0.3.3", mask=32, port=2)
        writeIPRules(p4info_helper, ingress_sw=sw[1], dst_eth_addr="00:00:00:00:02:02", dst_ip="10.0.2.2", mask=32, port=1)
        writeIPRules(p4info_helper, ingress_sw=sw[1], dst_eth_addr="00:00:00:03:03:00", dst_ip="10.0.3.3", mask=32, port=2)
        writeIPRules(p4info_helper, ingress_sw=sw[2], dst_eth_addr="00:00:00:00:03:03", dst_ip="10.0.3.3", mask=32, port=1)
        writeIPRules(p4info_helper, ingress_sw=sw[2], dst_eth_addr="00:00:00:01:03:00", dst_ip="10.0.1.1", mask=32, port=2)
        writeIPRules(p4info_helper, ingress_sw=sw[2], dst_eth_addr="00:00:00:02:03:00", dst_ip="10.0.2.2", mask=32, port=3)

        writeRecordRules(p4info_helper, ingress_sw=sw[0], qr_code=1)

        writeHash1Rule(p4info_helper, ingress_sw=sw[0])

        for s, mac in sw_mac.items():
            writePInRule(p4info_helper, ingress_sw=sw[int(s[1:])-1], etherType=0x88cc, sw_addr=mac)
            writePOutRule(p4info_helper, ingress_sw=sw[int(s[1:])-1], padding=0, sw_addr=mac)

        for j in range(0,len(sw)):
            for i in range(1,15):
                sendPacketOut(p4info_helper, sw[j], i, 0)

        for j in range(0,len(sw)):
            for i in range(0,14):
                recvPacketIn(sw[j])
            
        draw_topology(sw_mac, hosts)
        # print topology

        # writePInRule(p4info_helper, ingress_sw=sw[0], etherType=0x88cc, sw_addr="00:00:00:01:03:00")
        # writePInRule(p4info_helper, ingress_sw=sw[1], etherType=0x88cc, sw_addr="00:00:00:02:03:00")
        # writePInRule(p4info_helper, ingress_sw=sw[2], etherType=0x88cc, sw_addr="00:00:00:03:03:00")

        # writePOutRule(p4info_helper, ingress_sw=sw[0], padding=0, sw_addr="00:00:00:01:03:00")
        # writePOutRule(p4info_helper, ingress_sw=sw[1], padding=0, sw_addr="00:00:00:02:03:00")
        # writePOutRule(p4info_helper, ingress_sw=sw[2], padding=0, sw_addr="00:00:00:03:03:00")
 
            #############################################################################

        # connect to thrift
        # set s1 to gateway switch
        runtimeAPI = connectThrift(9090,bmv2_file_path)

        # set meter
        # runtimeAPI.do_meter_array_set_rates("meter_array_set_rates ingress_meter_stats 0.00000128:9000 0.00000128:9000")
        meter = runtimeAPI.get_res("meter", "ingress_meter_stats", runtime_CLI.ResType.meter_array)
        new_rates = []
        new_rates.append(runtime_CLI.BmMeterRateConfig(0.00000128, 9000))
        new_rates.append(runtime_CLI.BmMeterRateConfig(0.00000128, 9000))
        runtimeAPI.client.bm_meter_array_set_rates(0, meter.name, new_rates)



        m = 0
        total_res_num = 0
        while True:
            print "------------"
            print m," minute"
            now_res_num = read_register(runtimeAPI, "r_reg", 0)
            res_num = now_res_num - total_res_num
            total_res_num = now_res_num

            flag = read_register(runtimeAPI, "f_reg", 0)
            print "res_num: ", res_num
            print "flag: ", flag
            if res_num >= 10:
                if flag >= 5:
                    write_register(runtimeAPI, "f_reg", 0, flag+1)
                else:
                    write_register(runtimeAPI, "f_reg", 0, 5)
            elif res_num < 10 and flag > 0:
                write_register(runtimeAPI, "f_reg", 0, flag-1)

            if flag > 0:
                print "Mode on..."
                for i in range(0, 65536):
                    t_id = read_register(runtimeAPI, "reg_ingress", i)
                    if t_id > 0:
                        write_register(runtimeAPI, "reg_ingress", i, t_id-1)
                        print "reg[",i,"] = ",t_id-1

            # print "2nd res: ",read_register(runtimeAPI, "r_reg", 0)
            # write_register(runtimeAPI, "r_reg", 0, 0) # clean r_reg every minute
            m += 1
            sleep(30)


    except KeyboardInterrupt:
        print " Shutting down."
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()

if __name__ == '__main__': 
    # parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser = runtime_CLI.get_parser()
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/basic.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/basic.json')

    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print "\np4info file not found: %s\nHave you run 'make'?" % args.p4info
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print "\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json
        parser.exit(1)

    main(args.p4info, args.bmv2_json)
