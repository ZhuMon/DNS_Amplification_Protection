#!/usr/bin/env python
import sys 
import struct
import os
import threading

from scapy.all import *
from scapy.layers.inet import _IPOption_HDR

def get_if():
    ifs=get_if_list()
    iface=None
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print "Cannot find eth0 interface"
        exit(1)
    return iface

def handle_pkt(pkt, socket, r_pkt):
    if UDP in pkt and pkt[UDP].dport == 53:
        global r_num
        if r_num%10 == 1:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        elif r_num%10 == 2:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        elif r_num%10 == 3:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        else:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        r_num += 1
        sys.stdout.flush()
        pass_pkt(pkt, r_pkt[str(pkt[DNS].id)+str(pkt.qd)], socket)



def pass_pkt(q,r, socket):
    p = Ether(src = get_if_hwaddr(iface), dst="FF:FF:FF:FF:FF:FF")
    p = p / IP(dst=q[IP].src) / UDP(dport=q[UDP].sport, sport=53) / r.getlayer(DNS)
    global s_num
    if s_num%10 == 1:
        print "Send %4dst packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    elif s_num%10 == 2:
        print "Send %4dnd packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    elif s_num%10 == 3:
        print "Send %4drd packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    else:
        print "Send %4dth packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    s_num += 1
    sendp(p, iface = iface, verbose=False, socket=socket)

def distribute_thread(pkt, socket, r_pkt):
    tmp_pkt = dict(r_pkt)
    t = threading.Thread(target=handle_pkt, args=(pkt,socket,tmp_pkt,))
    t.setDaemon(True)
    t.start()

def main():
    ifaces = filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/'))
    global iface
    iface = ifaces[0]
    print("iface: ", iface)
    socket = conf.L2socket(iface=iface) 

    pcaps = rdpcap("dns0313_2_onlyDNS.pcapng")
    r_pkt = {}

    for pkt in pcaps:
        if pkt.qr == 1: # the packet is response
            r_pkt[str(pkt[DNS].id)+str(pkt.qd)] = pkt


    print "sniffing on %s" % iface
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: distribute_thread(x, socket, r_pkt))

if __name__ == '__main__':
    s_num = 0
    r_num = 0
    main()
