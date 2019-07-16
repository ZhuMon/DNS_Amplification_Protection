import argparse
import sys
import socket
import random
import struct

from scapy.all import *
from scapy.contrib import lldp
from ryu.topology.switches import LLDPPacket
#from scapy.all import sniff, sendp, send, get_if_list, get_if_hwaddr
#from scapy.all import Packet, IPOption
#from scapy.all import Ether, IP, UDP, TCP, DNS
#from scapy.all import rdpcap


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
        print "got a response"
        print pkt.show()
        sys.stdout.flush()

def Ge_lldp(port, padding):
    # mac1 = "{0:048b}".format(0)
    # mac2 = "{0:048b}".format(0)
    out1 = "{0:09b}".format(port)
    out2 = "{0:07b}".format(padding)
    out = out1 + out2
    return bytearray([int(out[0:8],2),int(out[8:16],2)])

def main():
    
    iface = get_if()
    print("iface: ", iface)


    # pkt = LLDPPacket.lldp_packet(45,23,get_if_hwaddr(iface),10)
    # p = Ether(_pkt=pkt)
    # p.show()
    pkt = Ether(type = 0x88cc)
    pkt = pkt/raw(Ge_lldp(23,0))
    # print len(p)
    pkt.show()
    sendp(pkt, iface = iface, verbose=False)

    # sniff(iface = iface, 
    #         prn = lambda x: handle_pkt(x),
    #         count = 1)


if __name__ == '__main__':
    main()
    
