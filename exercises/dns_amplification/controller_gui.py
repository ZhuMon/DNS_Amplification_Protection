import threading
import random
from time import sleep
from math import sqrt

from Tkinter import *
import ttk
from PIL import Image, ImageTk

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from event import myEvent

g_height = 1000
g_width = 700
rpktThreshold = 0


class ControllerGui():
    def __init__(self, event, sw_mac, h_mac, topology):
        """ init

        """
        self.event = event

        self.root = Tk()
        self.cv = Canvas(self.root,bg = 'white', height = g_height, width = g_width)
        self.fonts = ("arial", 12, "bold")

        self.var = StringVar()
        self.L1 = Label(self.root, textvariable=self.var, width=55, height=2)
        self.L1.place(x=120, y=500)

        #self.tree = ttk.Treeview(self.root, columns=('col1', 'col2', 'col3', 'col4') ,show='headings')
        self.tree = ttk.Treeview(self.root, columns=('col1', 'col2', 'col3') ,show='headings')
        self.tree.column('col1', width=150, anchor='center')
        self.tree.column('col2', width=150, anchor='center')
        self.tree.column('col3', width=50, anchor='center')
        #self.tree.column('col4', width=180, anchor='center')
        self.tree.heading('col1', text='mac_addr1')
        self.tree.heading('col2', text='mac_addr2')
        self.tree.heading('col3', text='ID')
        #self.tree.heading('col4', text='num of packet')

        self.sw_mac = sw_mac
        self.h_mac = h_mac
        self.topology = topology

        for no, link in sorted(self.topology.items()):
            mac1 = link.keys()[0]
            mac2 = link.keys()[1]
            self.tree.insert('', no, values=(mac1, mac2, no))
            #self.tree.insert('', no, values=(mac1, mac2, no, self.event.getPktNum(mac1, mac2)))
        
        self.tree.bind("<Double-1>", self.dbClick)

        self.ybar = ttk.Scrollbar(self.root, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.ybar.set)
        self.tree.place(x=100, y=650)
        self.ybar.place(x=450, y=650, height=218)
        #self.ybar.place(x=630, y=650, height=218)

        self.ge_network()

        self.node_size = 10
        self.create_node()

        self.button_quit = Button(self.root, text="Quit", fg='white', bg='red', font=self.fonts, command=self.quit)
        self.button_quit.place(x=500, y=830)

        self.button_refresh = Button(self.root, text="Refresh", fg='white', bg='green', font=self.fonts, command=self.refresh_network)
        self.button_refresh.place(x=500, y=800)

        self.cv.pack()
        self.cv.bind('<Motion>' , self.move_handler)

        self.edgeWarn_th = threading.Thread(target=self.edge_traffic_warn, args=(self.event,self.topology, self.cv))
        self.edgeWarn_th.setDaemon(True)
        self.edgeWarn_th.start()

        self.root.mainloop()

    def ge_network(self):
        """ generate network """

        self.G = nx.Graph()
        for s, mac in sorted(self.sw_mac.items()):
            self.G.add_node(mac.encode('utf-8'))

        for h, mac in sorted(self.h_mac.items()):
            self.G.add_node(mac.encode('utf-8'))

        edge = []
        for no, link in sorted(self.topology.items()):
            keys = link.keys()
            edge.append((keys[0],keys[1]))

        self.G.add_edges_from(edge)

        self.links = self.G.edges
        self.nodes = nx.spring_layout(self.G)
        

    def refresh_network(self):
        """ refresh network """

        self.G.clear()
        self.ge_network()

        self.cv.delete("all")
        self.create_node()
        #for no, link in sorted(self.topology.items()):
        #    mac1 = link.keys()[0]
        #    mac2 = link.keys()[1]
        #    pktNum = random.randint(1, 20)
        #    self.cv.itemconfig(self.event.getObjID(mac1, mac2), width=pktNum, fill="red")

    def create_node(self):
        """ create node """
        #img_sw = Image.open("Img/switch.png").resize((40, 40), Image.ANTIALIAS)
        # img_ctr = Image.open("Img/controller.png").resize((40, 40), Image.ANTIALIAS)
        #img_host = Image.open("Img/host.png").resize((40, 40), Image.ANTIALIAS)
        # img_pkt = Image.open("Img/packet.png").resize((40, 40), Image.ANTIALIAS)
        #self.photo_sw = ImageTk.PhotoImage(img_sw)
        # self.photo_ctr = ImageTk.PhotoImage(img_ctr)
        #self.photo_host = ImageTk.PhotoImage(img_host)
        # self.photo_pkt = ImageTk.PhotoImage(img_pkt)

        for node, pos in self.nodes.items():
            pos[0] = (self.extend(pos[0], 'x')+2)*125
            pos[1] = (self.extend(pos[1], 'y')+2)*125

        self.linkID = []

        for link in self.links:
            No = self.cv.create_line(self.nodes[link[0]][0]+self.node_size/2, self.nodes[link[0]][1]+self.node_size/2, self.nodes[link[1]][0]+self.node_size/2, self.nodes[link[1]][1]+self.node_size/2)
            self.linkID.append(No)
            self.event.putObjID(No, link[0], link[1])

        self.switches = []
        self.hosts = []
        for node, pos in self.nodes.items():
            if node[15:] == "00" :
                # sw = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_sw)
                sw = self.cv.create_oval(pos[0], pos[1], pos[0]+self.node_size, pos[1]+self.node_size, fill="white")
                self.switches.append(sw)
            else:
                host = self.cv.create_polygon(pos[0], pos[1], pos[0], pos[1]+self.node_size, pos[0]+self.node_size, pos[1]+self.node_size, pos[0]+self.node_size, pos[1])
                # host = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_host)
                self.hosts.append(host)

    def extend(self, num, axis='x'):
        """ expand network size """
        if num < 0:
            num = abs(num)
            return sqrt(num) * sqrt(2) * (-1)
        else:
            return sqrt(num) * sqrt(2)

    def edge_traffic_warn(self, event, topology, cv):
        """ detect which edge is busy, warn user via color changing """
        while event.is_set() is True:
            for no, link in sorted(topology.items()):
                mac1 = link.keys()[0]
                mac2 = link.keys()[1]
                pktNum = event.getPktNum(mac1, mac2)
                if pktNum > rpktThreshold:
                    cv.itemconfig(event.getObjID(mac1, mac2), width=pktNum, fill="red")
            for i in range(0, 10):
                if event.is_set() is False:
                    break
                sleep(1)

    def dbClick(self, event):
        """ double click one row """
        self.item = self.tree.selection()[0]
        print "you clicked on ", self.tree.item(self.item, "values")
                
    def quit(self):
        #TODO clear others 
        self.G.clear()
        self.cv.delete("all")
        self.root.destroy()
        self.event.clear()
        # exit()

    def move_handler(self, event):
        """ detect if mouse is focus, show information """
        self.var.set('')
        
        for node, pos in self.nodes.items():
            if  pos[0] < event.x < pos[0]+self.node_size and pos[1] < event.y < pos[1]+self.node_size:
                if node[15:] == "00" :
                    self.var.set("Switch Mac: "+node)
                else:
                    self.var.set("Host Mac: "+node)
                break
            #elif 

def main():

    sw_mac = {'s16': '00:00:00:10:15:00', 's9': '00:00:00:09:15:00', 's8': '00:00:00:08:15:00', 's17': '00:00:00:11:15:00', 's3': '00:00:00:03:15:00', 's2': '00:00:00:02:15:00', 's1': '00:00:00:01:15:00', 's10': '00:00:00:0a:15:00', 's7': '00:00:00:07:15:00', 's6': '00:00:00:06:15:00', 's5': '00:00:00:05:15:00', 's4': '00:00:00:04:15:00', 's13': '00:00:00:0d:15:00', 's20': '00:00:00:14:15:00', 's18': '00:00:00:12:15:00', 's15': '00:00:00:0f:15:00', 's12': '00:00:00:0c:15:00', 's19': '00:00:00:13:15:00', 's21': '00:00:00:15:15:00', 's14': '00:00:00:0e:15:00', 's11': '00:00:00:0b:15:00'}
    
    h_mac = {u'h8': u'00:00:00:00:0c:08', u'h9': u'00:00:00:00:0d:09', u'h7': u'00:00:00:00:0b:07', u'h1': u'00:00:00:00:01:01', u'h6': u'00:00:00:00:0a:06', u'h12': u'00:00:00:00:10:0c', u'h13': u'00:00:00:00:12:0d', u'h14': u'00:00:00:00:13:0e', u'h15': u'00:00:00:00:15:0f', u'h4': u'00:00:00:00:07:04', u'h5': u'00:00:00:00:08:05', u'h10': u'00:00:00:00:0e:0a', u'h2': u'00:00:00:00:02:02', u'h11': u'00:00:00:00:0f:0b', u'h3': u'00:00:00:00:03:03'}

    topology = {'24': {'00:00:00:04:15:00': 1, '00:00:00:0b:15:00': 2}, '25': {'00:00:00:04:15:00': 2, '00:00:00:0c:15:00': 2}, '26': {'00:00:00:04:15:00': 3, '00:00:00:0d:15:00': 2}, '27': {'00:00:00:0e:15:00': 2, '00:00:00:04:15:00': 4}, '20': {'00:00:00:07:15:00': 2, '00:00:00:04:15:00': 12}, '21': {'00:00:00:08:15:00': 2, '00:00:00:04:15:00': 13}, '22': {'00:00:00:09:15:00': 2, '00:00:00:04:15:00': 14}, '23': {'00:00:00:0a:15:00': 2, '00:00:00:09:15:00': 1}, '28': {'00:00:00:0f:15:00': 2, '00:00:00:04:15:00': 5}, '29': {'00:00:00:10:15:00': 2, '00:00:00:04:15:00': 6}, '1': {u'00:00:00:00:12:0d': 1, '00:00:00:12:15:00': 1}, '0': {'00:00:00:13:15:00': 1, u'00:00:00:00:13:0e': 1}, '3': {'00:00:00:0d:15:00': 1, u'00:00:00:00:0d:09': 1}, '2': {'00:00:00:08:15:00': 1, u'00:00:00:00:08:05': 1}, '5': {'00:00:00:01:15:00': 1, u'00:00:00:00:01:01': 1}, '4': {u'00:00:00:00:0c:08': 1, '00:00:00:0c:15:00': 1}, '7': {'00:00:00:07:15:00': 1, u'00:00:00:00:07:04': 1}, '6': {'00:00:00:0a:15:00': 1, u'00:00:00:00:0a:06': 1}, '9': {u'00:00:00:00:0f:0b': 1, '00:00:00:0f:15:00': 1}, '8': {u'00:00:00:00:10:0c': 1, '00:00:00:10:15:00': 1}, '11': {u'00:00:00:00:03:03': 1, '00:00:00:03:15:00': 1}, '10': {'00:00:00:0e:15:00': 1, u'00:00:00:00:0e:0a': 1}, '13': {u'00:00:00:00:02:02': 1, '00:00:00:02:15:00': 1}, '12': {u'00:00:00:00:15:0f': 1, '00:00:00:15:15:00': 1}, '15': {'00:00:00:05:15:00': 1, '00:00:00:02:15:00': 2}, '14': {u'00:00:00:00:0b:07': 1, '00:00:00:0b:15:00': 1}, '17': {'00:00:00:05:15:00': 3, '00:00:00:04:15:00': 10}, '16': {'00:00:00:05:15:00': 2, '00:00:00:03:15:00': 2}, '19': {'00:00:00:06:15:00': 2, '00:00:00:04:15:00': 11}, '18': {'00:00:00:01:15:00': 2, '00:00:00:06:15:00': 1}, '31': {'00:00:00:11:15:00': 1, '00:00:00:12:15:00': 2}, '30': {'00:00:00:11:15:00': 2, '00:00:00:04:15:00': 7}, '34': {'00:00:00:14:15:00': 1, '00:00:00:15:15:00': 2}, '33': {'00:00:00:04:15:00': 9, '00:00:00:14:15:00': 2}, '32': {'00:00:00:04:15:00': 8, '00:00:00:13:15:00': 2}}

    event = myEvent(topology)
    c = ControllerGui(event, sw_mac, h_mac, topology)
if __name__ == '__main__':
    main()
