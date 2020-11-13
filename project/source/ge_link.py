import json
import os
import sys
from time import sleep

sys.path.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '../../utils/'))
sys.path.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '../../utils/p4runtime_lib'))
from run_exercise import *

def parse_link(unparsed_links):
    links = []
    for link in unparsed_links:
        s, t = link[0], link[1]
        if s > t:
            s,t = t,s

        link_dict = {'node1':s,
                    'node2':t}
        links.append(link_dict)

    host_links = []
    switch_links = []
    global sw_port_mapping
    sw_port_mapping = {}

    for link in links:
        if link['node1'][0] == 'h':
            host_links.append(link)
        else:
            switch_links.append(link)

    link_sort_key = lambda x: x['node1'] + x['node2']

    host_links.sort(key = link_sort_key)
    switch_links.sort(key = link_sort_key)

    host_file = open("host.json", "w")

    for link in host_links:
        host_name = link['node1']
        host_sw   = link['node2']
        host_num = int(host_name[1:])
        sw_num   = int(host_sw[1:])
        host_ip = "10.0.%d.%d" % (sw_num, host_num)
        host_mac = '00:00:00:00:%02x:%02x' % (sw_num, host_num)
        
        addSwitchPort(host_sw, host_name, host_ip, host_mac)

    host_file.write(json.dumps(sw_port_mapping, sort_keys = True, indent=4, separators=(',', ': ')))


def addSwitchPort(sw, node2, ip, mac):
    if sw not in sw_port_mapping:
        sw_port_mapping[sw] = {}

    portno = len(sw_port_mapping[sw])+1
    sw_port_mapping[sw][portno] = {"name":node2,"ip":ip, "mac":mac}

def main():
    json_file = open("topology.json", "r")
    topology = json.load(json_file)

    sw_file = open("switch.txt", "w")

    hosts = topology["hosts"]
    parse_link(topology["links"])
    switches = topology["switches"]

    for i in range(1,len(switches)+1):
        sw_file.write("s%d 00:00:00:%02x:%02x:00\n"% (i,i,len(switches)))
        
    


if __name__ == "__main__":
    main()
