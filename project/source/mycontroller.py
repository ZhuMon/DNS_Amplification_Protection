#!/usr/bin/env python2
import argparse
import grpc
import os
import sys
import time
from time import sleep
import signal
import json
from threading import Thread

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper
import runtime_CLI
import bmpy_utils as utils

from scapy.all import *
from scapy.contrib import lldp
from scapy.config import conf
from scapy.packet import bind_layers

from Tkinter import *
import tkMessageBox as messagebox
from ttk import *

import networkx as nx

from controller_gui import ControllerGui
from event import myEvent

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2

topology = {}
link_num = 0
mac_portNum = {} # {mac: 2, mac1: 3}
sw_mac = {}      # {s1: mac, ...} 
hosts = {}       # {h1: mac, ...}
host_ip = {}     # {h1: ip, ...}
sw_links = {}    # {s1: [[1,h1],[2,h5]], s2:...}
direction = {}   # {1: {mac1: 'q', mac2: 'r'}, 2: ...}
API = {}         # runtimeAPI {s1: connectThrift.. , s2...}

        
        
def GePacketOut(egress_port, mcast, padding):
    """ Generate packet_out packet with bytearray format """

    out1 = "{0:09b}".format(egress_port)
    out2 = "{0:016b}".format(mcast)
    out3 = "{0:07b}".format(padding)
    out = out1+out2+out3
    a = bytearray([int(out[0:8],2),int(out[8:16],2),int(out[16:24],2),int(out[24:32],2)])
    return a

def ParsePacketIn(pin):
    """ 
        Parse packet_in packet with bytearray format to dictionary
        byte<6>:dstAddr
        byte<6>:srcAddr
        byte<2>:type
        bit<9>:sport
        bit<9>:dport
        bit<6>:padding
    """
    

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
    """
        After got a packet_in, record the link in topology
    """

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
        
def sendPacketOut(p4info_helper, sw, port, mcast, padding):
    """ send packet_out from controller to switch """
    packet = GePacketOut(port, mcast, padding) #padding must be 0
    packet_out = p4info_helper.buildPacketOut(payload = str(packet))
    # print packet_out
    sw.SendPktOut(packet_out)

def recvPacketIn(sw):
    """ Handle receiving packet_in from switch """
    try:
        content = sw.RecvPktIn()
        if content != None and content.WhichOneof('update')=='packet':
            packet = content.packet.payload
            pkt = bytearray(packet)
            p = ParsePacketIn(pkt)
            recordLink(p)
    except Exception, e:
        None

################## Write Rule on switch ###################

def writeIPRules(p4info_helper, ingress_sw, dst_eth_addr, dst_ip, mask, port):
    """ Install ip packet transfer rule on switch """
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
    """ Install record num of dns_reponse_packet rule on switch """

    table_entry = p4info_helper.buildTableEntry(
        table_name = "MyIngress.dns_response_record",
        match_fields = {
            "hdr.dns.qr": qr_code
        },
        action_name = "MyIngress.record_response"
        )
    ingress_sw.WriteTableEntry(table_entry)

def writeIPFrRule(p4info_helper, ingress_sw, macAddr):
    """ Install "count num of query packet with same IP" rule on switch """
    table_entry = p4info_helper.buildTableEntry(
        table_name = "MyIngress.ip_frequency_table",
        match_fields = {
            "hdr.dns.qr": 1
        },
        action_name = "MyIngress.record_ip_f",
        )
    ingress_sw.WriteTableEntry(table_entry)
    
def writePInRule(p4info_helper, ingress_sw, etherType, sw_addr):
    """ Install switch send back to controller rule on switch """
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
    """ Install "handle packet_out packet" rule on switch"""
    if padding == 0: # send to another switch
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
    elif padding == 1: # send back to controller
        table_entry = p4info_helper.buildTableEntry(
            table_name = "MyIngress.pkt_out_table",
            match_fields = {
                "hdr.packet_out.padding": padding
            },
            action_name = "MyIngress.response_to_cpu",
            action_params={
                "swAddr": sw_addr
            })
        ingress_sw.WriteTableEntry(table_entry)

def setMeter(runtimeAPI):
    """  set meter """
    # runtimeAPI.do_meter_array_set_rates("meter_array_set_rates MyIngress.ingress_meter_stats 0.00000128:9000 0.00000128:9000")
    meter = runtimeAPI.get_res("meter", "ingress_meter_stats", runtime_CLI.ResType.meter_array)
    new_rates = []
    new_rates.append(runtime_CLI.BmMeterRateConfig(0.00000128, 9000))
    new_rates.append(runtime_CLI.BmMeterRateConfig(0.00000128, 9000))
    runtimeAPI.client.bm_meter_array_set_rates(0, meter.name, new_rates)

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
    """ read register by thrift """
    reg = runtimeAPI.get_res("register", name, 
                            runtime_CLI.ResType.register_array)
    return runtimeAPI.client.bm_register_read(0, reg.name, index)

def write_register(runtimeAPI, name, index, value):
    """ write register by thrift """
    register = runtimeAPI.get_res("register", name, 
                            runtime_CLI.ResType.register_array)
    runtimeAPI.client.bm_register_write(0, register.name, index, value)

def connectThrift(port, bmv2_file_path):
    """ use runtimeCLI to connect Thrift """
    standard_client, mc_client = utils.thrift_connect(
        'localhost', port,
        runtime_CLI.RuntimeAPI.get_thrift_services(runtime_CLI.PreType.SimplePre)
    )

    runtime_CLI.load_json_config(standard_client, bmv2_file_path)
    return runtime_CLI.RuntimeAPI(runtime_CLI.PreType.SimplePre, standard_client, mc_client)

def record_switch_port():
    """ 
        record how many port the switch/host has used
        mac_portNum = {mac:num(port), ...}
    """
    tmp = {} # {mac1: [2,1,3], ...}
    for no, links in topology.items():
        m1 = links.keys()[0]
        m2 = links.keys()[1]
        if tmp.has_key(m1) is False:
            tmp[m1] = []
        if tmp.has_key(m2) is False:
            tmp[m2] = []
        
        tmp[m1].append(links[m1])
        tmp[m2].append(links[m2])

    for mac, port in tmp.items():
        mac_portNum[mac] = len(port)
    
def find_the_other_mac(mac1, port1):
    """ FROM mac and port TO find the mac at the other side """

    for no, link in topology.items():
        m1 = link.keys()[0]
        m2 = link.keys()[1]
        p1 = link.values()[0]
        p2 = link.values()[1]
        if mac1 == m1 and port1 == p1:
            return m2
        elif mac1 == m2 and port1 == p2:
            return m1
    
def mac2name(mac):
    """ mac -> name """
    for sw, m in sw_mac.items():
        if mac == m:
            return sw
    for h, m in hosts.items():
        if mac == m:
            return h

def read_all_reg(event, bmv2_file_path, sw_num):

    while event.is_set():
        event.cleanFlag()
        while event.controller_lock == False:
            None
        event.controller_lock = False

        for mac, portNum in mac_portNum.items():
            if mac2name(mac)[0] == 'h':
                continue
            for port in range(1, int(portNum)+1):
                sw = mac2name(mac)

                mac2 = find_the_other_mac(mac, port)

                r_num = read_register(API[sw], "r_reg", port)
                q_num = read_register(API[sw], "rq_reg", port)
                
                if event.isUpdated(mac, mac2, 'q') is False:
                    event.putPktNum(q_num, mac, mac2, 'q')
                    n = event.getPktNum(mac, mac2, 'q')
                if event.isUpdated(mac, mac2, 'r') is False:
                    event.putPktNum(r_num, mac, mac2, 'r')
                    n = event.getPktNum(mac, mac2, 'r')

        event.controller_lock = True

        for i in range(0, 10):
            if event.is_set() is False:
                break
            sleep(1)

def find_path(p4info_helper, sw, host_ip):
    """ 
        find all path of node to the other node 
        and write rule on switches
    """
    for no, links in topology.items():
        m1 = mac2name(links.keys()[0])
        m2 = mac2name(links.keys()[1])
        p1 = links.values()[0]
        p2 = links.values()[1]
        if sw_links.has_key(m1) is False:
            sw_links[m1] = [[p1,m2]]
        else:
            sw_links[m1].append([p1, m2])

        if sw_links.has_key(m2) is False:
            sw_links[m2] = [[p2,m1]]
        else:
            sw_links[m2].append([p2, m1])

    path = {} # {s1: { h1: [1,2,4,2,1], h2: [...]}, s2:...}
    for s, s_mac in sw_mac.items():
        s = s.encode('utf-8')
        path[s] = {}
        for h, h_mac in hosts.items():
            h = h.encode('utf-8')
            h_mac = h_mac.encode('utf-8')
            path[s][h] = [] # [1, 2, 10, 2, 1]
            stack = [s]      # [s2, s4...]
            stack, path[s][h] = recursive(s, h, stack, path[s][h])
            # print path[s][h] 
            dst_eth_addr = find_the_other_mac(s_mac, path[s][h][0]).encode('utf-8')
            writeIPRules(p4info_helper, ingress_sw=sw[int(s[1:])-1], dst_eth_addr= dst_eth_addr, dst_ip=host_ip[h].encode('utf-8'), mask=32, port=path[s][h][0])
            # print s, "->", h_mac, dst_eth_addr, path[s][h][0]
        writeRecordRules(p4info_helper, ingress_sw=sw[int(s[1:])-1], qr_code=1)

def recursive(src, dst, stack, path):
    """ for find_path """
    if stack != [] and stack[len(stack)-1] == dst:
        return stack, path

    for link in sw_links[src]:
        if link[1] == dst:
            path.append(link[0])
            stack.append(link[1])
            break
        if link[1] not in stack:
            stack.append(link[1])
            path_tmp = list(path)
            path.append(link[0])
            stack, path = recursive(link[1], dst, stack, path)
            if stack[len(stack)-1] == dst:
                break
            else:
                path = path_tmp
    
    return stack, path

def find_qr_path():
    """ find direction of packet on each link """
    for no, link in topology.items():
        mac1 = link.keys()[0]
        mac2 = link.keys()[1]
        n1 = mac2name(mac1)
        n2 = mac2name(mac2)
        stack1 = [n1] 
        path1 = []
        stack1, path1 = recursive(n1, "h3", stack1, path1)
        stack2 = [n2] 
        path2 = []
        stack2, path2 = recursive(n2, "h3", stack2, path2)
        direction[no] = {}
        if len(path1) > len(path2):
            direction[no][mac1] = 'q'
            direction[no][mac2] = 'r'
        else:
            direction[no][mac1] = 'r'
            direction[no][mac2] = 'q'

def num2ip(num):
    """ num(16670061) to IP(10.0.0.1) """
    num_x = "{0:08x}".format(num)
    num_str = str(num_x)
    ip = ""
    for i in [0,2,4,6]:
        a = int(num_str[i:i+2],16)
        ip += str(a)
        if i != 6:
            ip += '.'

    return ip

def ip2name(ip_in):
    """ ip(10.0.1.1) to name(h1) """
    for h, ip in host_ip.items():
        if ip_in == ip:
            return h
    print "can't find ip:",ip_in,"in ip2name"

def main(event, p4info_file_path='./build/basic.p4.p4info.txt' ,bmv2_file_path='./build/basic.json'):
    """
        main function
    """

    global topology, link_num, mac_portNum, sw_mac
    global hosts, host_ip, sw_links, direction, API
    topology = {}
    link_num = 0
    mac_portNum = {} # {mac: 2, mac1: 3}
    sw_mac = {}      # {s1: mac, ...} 
    hosts = {}       # {h1: mac, ...}
    host_ip = {}     # {h1: ip, ...}
    sw_links = {}    # {s1: [[1,h1],[2,h5]], s2:...}
    direction = {}   # {1: {mac1: 'q', mac2: 'r'}, 2: ...}
    API = {}         # runtimeAPI {s1: connectThrift.. , s2...}

    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)


    try:
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
        
        
        
        with open("host.json", "r") as host_file:
            host_inf = json.load(host_file)
            for s, sw_inf in host_inf.items():
                for port, p_inf in sw_inf.items():
                    recordLink({"srcAddr":sw_mac[s], "sport":int(port),
                                 "dstAddr":p_inf["mac"], "dport":1})
                    hosts[p_inf["name"]] = p_inf["mac"]
                    host_ip[p_inf["name"]] = p_inf["ip"]

        # re-Master
        for i in range(0, len(sw)):
            sw[i].MasterArbitrationUpdate()

        # install rules
        for s, mac in sw_mac.items():
            writePInRule(p4info_helper, ingress_sw=sw[int(s[1:])-1], etherType=0x88cc, sw_addr=mac)
            writePOutRule(p4info_helper, ingress_sw=sw[int(s[1:])-1], padding=0, sw_addr=mac)
            writePOutRule(p4info_helper, ingress_sw=sw[int(s[1:])-1], padding=1, sw_addr=mac)

        # detect topology
        for j in range(0,len(sw)):
            for i in range(1,15):
                sendPacketOut(p4info_helper, sw[j], i, 0, 0)
        for j in range(0,len(sw)):
            for i in range(0,14):
                recvPacketIn(sw[j])
        
        # re-Master
        for i in range(0, len(sw)):
            sw[i].MasterArbitrationUpdate()


        # s4 is gateway switch
        writeIPFrRule(p4info_helper, ingress_sw = sw[3], macAddr = sw_mac['s4'])

        find_path(p4info_helper, sw, host_ip)
        record_switch_port()
        find_qr_path()

        # build runtimeCLI
        for s, mac in sw_mac.items():
            runtimeAPI = connectThrift(9089+int(s[1:]),bmv2_file_path)
            API[s] = runtimeAPI

            
        # init threads
        event.init(topology, direction, sw_links)
        event.set()
        event.recordName(hosts,sw_mac)

        gui_th = Thread(target=ControllerGui, args=(event, sw_mac, hosts, topology))
        gui_th.setDaemon(True)

        reg_th = Thread(target=read_all_reg, args=(event, bmv2_file_path,len(sw_mac)))
        reg_th.setDaemon(True)

        reg_th.start()
        gui_th.start()

 
            #############################################################################

        # connect to thrift
        # set s4 to gateway switch
        runtimeAPI = API['s4']
        setMeter(runtimeAPI)

            
        m = 0
        quick_cool_down = {}
        quick_cool_down['s4'] = 0
        rule_has_set = {}
        rule_has_set['s4'] = True
        active_API = {}
        active_API['s4'] = runtimeAPI
        aboutClose = 0
        s_reg_i = {} # record s_reg index of new switch 
        while event.is_set() is True:

            print "=================="
            print m*10,"second"

            while event.controller_lock is False:
                None
            event.controller_lock = False

            thr_res_num = event.thr_res_num
            if event.getMeterFlag() == 1:
                for sw_name, api in active_API.items():
                    
                    res_num = event.getPktNum(sw_mac[sw_name], None, 'r')
                    flag = read_register(api, "f_reg", 0)

                    if res_num >= thr_res_num:
                        quick_cool_down[sw_name] = 0
                        if flag >= 5:
                            flag += 1
                        else:
                            flag = 5

                        write_register(api, "f_reg", 0, flag)

                    elif res_num < thr_res_num and flag > 0 and quick_cool_down[sw_name] >= 3:
                        # print "less response num... quick cool down"
                        write_register(api, "f_reg", 0, int(flag/2))
                        flag = int(flag/2)
                    elif res_num < thr_res_num and flag > 0:
                        write_register(api, "f_reg", 0, flag-1)
                        flag -= 1
                        quick_cool_down[sw_name] += 1
                    
                    print "------------"
                    print sw_name,"res_num: ", res_num
                    print "flag: ", flag
                    print "threshold: ", thr_res_num

                    if flag > 0:
                        print sw_name,"mode on..."

                        if sw_name == "s4" and flag == 1:
                            aboutClose = 1
                        elif sw_name == "s4":
                            aboutClose = 0
                        # for i in range(0, 65536):
                            # t_id = read_register(api, "reg_ingress", i)
                            # if t_id > 0:
                        #         write_register(api, "reg_ingress", i, t_id-1)
                                    # print "reg[",i,"] = ",t_id-1
                    else:
                        # clean API...
                        if sw_name != "s4":
                            
                            write_register(runtimeAPI, "s_reg", s_reg_i[sw_name], 0)
                            s_reg_i.pop(sw_name)
                            rule_has_set[sw_name] = False
                            quick_cool_down[sw_name] = 0
                            active_API.pop(sw_name)
                        elif aboutClose == 1:
                            aboutClose = 0
                            for i in range(0, 65536):
                                write_register(api, "reg_ingress", i, 0)

                for i in range(0, 256):
                    f = read_register(runtimeAPI, "fr_reg", i)
                    if f > 300:
                        num = read_register(runtimeAPI, "s_reg", i) # get a host
                        if num == 0:
                            sleep(1)
                            num = read_register(runtimeAPI, "s_reg", i)
                        ip = num2ip(num) # find the ip of the host from num
                        name = ip2name(ip)# find the host name
                        s = sw_links[name][0][1] # find switch the host connect

                        if rule_has_set.has_key(s) is False or rule_has_set[s] == False:
                            print "Add new switch to help :",s
                            setMeter(API[s])
                            sw[int(s[1:])-1].MasterArbitrationUpdate()
                            active_API[s] = API[s]
                            rule_has_set[s] = True
                            quick_cool_down[s] = 0
                            s_reg_i[s] = i
                            write_register(API[s], "f_reg", 0, 5)
                            
                            
                    write_register(runtimeAPI, "fr_reg", i, 0) # clean
            else: # clean flag
                for s,api in active_API.items():
                    write_register(api, "f_reg", 0, 0)

            event.controller_lock = True

            m += 1
            for i in range(0, 10):
                if event.is_set() is False:
                    break
                sleep(1)

    except KeyboardInterrupt:
        print " Shutting down."
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()
    print "====== Close Controller ======"

if __name__ == '__main__': 
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

    event = myEvent()
    main(event)
