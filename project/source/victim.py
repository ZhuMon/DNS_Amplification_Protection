import argparse
import sys
import socket
import random
import time
import struct
import threading

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

def handle_pkt(pkt):
    if UDP in pkt and pkt[UDP].sport == 53:
        global num
        num = num + 1
        if num%10 == 1:
            print "Get  %4dst packet, id: %5d"%(num,pkt.getlayer(DNS).id)
        elif num%10 == 2:
            print "Get  %4dnd packet, id: %5d"%(num,pkt.getlayer(DNS).id)
        elif num%10 == 3:
            print "Get  %4drd packet, id: %5d"%(num,pkt.getlayer(DNS).id)
        else:
            print "Get  %4dth packet, id: %5d"%(num,pkt.getlayer(DNS).id)

        sys.stdout.flush()

def recv_pkt(iface):
    try:
        sniff(iface = iface, prn = lambda x: handle_pkt(x))
    except KeyboardInterrupt:
        sys.exit(0)

def main():
    
    addr = "10.0.3.3"
    iface = get_if()
    print("iface: ", iface)

    pcap = rdpcap("dns0313_2_onlyDNS.pcapng")

    q_pkt = []
    for pkt in pcap:
        if pkt.qr == 0: # the packet is query
            q_pkt.append(pkt)

    recv_th = threading.Thread(target=recv_pkt, args=(iface,))
    recv_th.setDaemon(True)
    recv_th.start()

    try:
        N = raw_input()
        socket = conf.L2socket(iface=iface) 
        for i in range(0,int(N)):
            a = raw_input()
            b = raw_input()
            pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
            pkt = pkt /IP(dst=addr) / UDP(dport=53, sport=random.randint(49152,65535)) / q_pkt[int(b)].getlayer(DNS)
            
            sendp(pkt, iface = iface, verbose=False, socket=socket)
            if i%10 == 1:
                print "Send %4dst packet, id: %5d"%(i,pkt.getlayer(DNS).id)
            elif i%10 == 2:
                print "Send %4dnd packet, id: %5d"%(i,pkt.getlayer(DNS).id)
            elif i%10 == 3:
                print "Send %4drd packet, id: %5d"%(i,pkt.getlayer(DNS).id)
            else:
                print "Send %4dth packet, id: %5d"%(i,pkt.getlayer(DNS).id)

            time.sleep(float(a))
            
        while True:
            None
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    num = 0
    main()
    
