import threading
import random
from time import sleep
from math import sqrt,cos,sin,pi
from functools import partial

from Tkinter import *
import tkMessageBox as messagebox
from ttk import *
from PIL import Image, ImageTk

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from event import myEvent

win_size = '1100x600'
g_height = 600
g_width = 1100
fr_topo_height = 400
fr_topo_width = 400
qpktThreshold = 0
rpktThreshold = 0 
modes = ["Mitigation On","Mitigation Off"]

def assign(obj, **kwargs):
    obj.__dict__.update(kwargs)

class Object(object):
    def __init__(self, **kwargs):
        assign(self, **kwargs)

class MyScrollbar(Scrollbar, object):
    def __init__(self, parent, canvas, nodes, node_size, shohid="", orient="horizental", command=None):
        super(MyScrollbar, self).__init__(parent, orient=orient, command=command)
        self.cv = canvas
        self.nodes = nodes
        self.node_size = node_size
        self.orient = orient
        self.shohid = shohid

    def set(self, a, b, nodes={}, node_size=10, shohid=""):
        super(MyScrollbar, self).set(a,b)
        self.node_size = node_size
        self.nodes = nodes
        self.shohid
        if self.cv.labelGw != None:
            self.cv.labelGw.place_forget()
            self.cv.labelRt.place_forget()
            self.cv.labelSv.place_forget()
            self.cv.labelVt.place_forget()
            self.cv.labelCt.place_forget()
            x0 = self.cv.canvasx(0)
            y0 = self.cv.canvasy(0)
            for node, pos in self.nodes.items():
                wx = pos[0]-x0
                wy = pos[1]-y0
                if node[15:] == "00" :
                    if node[0:] == "00:00:00:04:15:00":
                        self.cv.labelGw.place(x=wx , y=wy+self.node_size)
                        self.cv.labelCt.place(x=wx+6*self.node_size, y=10*self.node_size+wy+sqrt(3)*self.node_size)
                    if node[0:] == "00:00:00:05:15:00":
                        self.cv.labelRt.place(x=wx , y=wy+self.node_size)
                else:
                    if node[0:] == "00:00:00:00:03:03":
                        self.cv.labelSv.place(x=wx , y=wy+self.node_size)
                    if node[0:] == "00:00:00:00:01:01":
                        self.cv.labelVt.place(x=wx , y=wy+self.node_size)
        if self.shohid == "show":
            self.cv.labelGw.place_forget()
            self.cv.labelRt.place_forget()
            self.cv.labelSv.place_forget()
            self.cv.labelVt.place_forget()
            self.cv.labelCt.place_forget()
#        if self.shohid == "hide":
#            self.cv.labelGw.place_forget()
#            self.cv.labelRt.place_forget()
#            self.cv.labelSv.place_forget()
#            self.cv.labelVt.place_forget()
#            self.cv.labelCt.place_forget()
#            for node, pos in self.nodes.items():
#                wx = pos[0]-x0
#                wy = pos[1]-y0
#                if node[15:] == "00" :
#                    if node[0:] == "00:00:00:04:15:00":
#                        self.cv.labelGw.place(x=wx , y=wy+self.node_size)
#                        self.cv.labelCt.place(x=wx+6*self.node_size, y=10*self.node_size+wy+sqrt(3)*self.node_size)
#                    if node[0:] == "00:00:00:05:15:00":
#                        self.cv.labelRt.place(x=wx , y=wy+self.node_size)
#                else:
#                    if node[0:] == "00:00:00:00:03:03":
#                        self.cv.labelSv.place(x=wx , y=wy+self.node_size)
#                    if node[0:] == "00:00:00:00:01:01":
#                        self.cv.labelVt.place(x=wx , y=wy+self.node_size)

           

class ControllerGui():
    def __init__(self, event, sw_mac, h_mac, topology):
        """ init 

        """
        self.event = event
        self.root = Toplevel()
        self.root.title("Controller GUI")
        self.root.geometry(win_size)

        self.sw_mac = sw_mac
        self.h_mac = h_mac
        self.topology = topology


        self.initStyle()

        self.fr_bg = Frame(self.root, height = g_height-100, width = g_width)
        self.fr_tp = Frame(self.fr_bg, height = 100, width = g_width)
        # self.fr_tb = Frame(self.fr_bg, height = g_height-100, width = g_width/2)
        
        self.cv_tp = Canvas(self.fr_bg, height = 100, width = g_width,highlightthickness=0)
        self.cv_tp.create_image(0,0, image=self.t_bgPhoto, anchor = "nw")
        
        self.fr_topo = Frame(self.fr_bg, height = fr_topo_height, width = fr_topo_width)
        self.cv_topo = Canvas(self.fr_topo,bg = self.bg, height = fr_topo_height, width = fr_topo_width, highlightthickness=0)
        self.cv_topo.create_image(0,0, image=self.topo_bgPhoto, anchor="nw")
        self.cv_topo.labelGw = None
        self.cv_topo.labelRt = None
        self.cv_topo.labelSv = None
        self.cv_topo.labelVt = None
        self.cv_topo.labelCt = None

        self.fr_mid = Frame(self.fr_bg, height = 400, width = 300, style="TFrame")

        self.fr_table = Frame(self.fr_bg, height = 400, width = 400)

        self.cv_btm= Canvas(self.fr_tp, height = 100, width = g_width,highlightthickness=0)
        self.cv_btm.create_image(0,0, image=self.b_bgPhoto, anchor = "nw")
        



        self.var = StringVar()
        self.L1 = Label(self.fr_mid, textvariable=self.var, width=30, anchor="center", background=self.bg)

        self.thres = Label(self.fr_mid, text="Threshold:", anchor="center", background=self.bg)

        self.zoom = Object(x1=0, y1=0, x2=0, y2=0, area=0, 
                rect=self.cv_topo.create_rectangle(0,0,0,0), 
                width = fr_topo_width, 
                height = fr_topo_height)
        self.zoomState = "Not"
        self.zoomIn = Button(self.fr_mid, style="in.zoom.TButton", command=partial(self.topoZoom, InOut="in"))
        self.zoomOut = Button(self.fr_mid, style="out.zoom.TButton", command=partial(self.topoZoom, InOut="out"))

        
        self.usrIn = StringVar()
        self.usrIn.set("")
        self.thresIn = Entry(self.fr_mid, textvariable=self.usrIn, width=8, font=self.fonts)
        self.enter = Button(self.fr_mid, text="Enter", command=self.getThreshold, width=5)

        self.tree = Treeview(self.fr_table, columns=('col1', 'col2', 'col3', 'col4') ,show='headings')
        self.ybar = Scrollbar(self.fr_table, orient=VERTICAL, command=self.tree.yview)
        self.tree.column('col1', width=100, anchor='center')
        self.tree.column('col2', width=100, anchor='center')
        self.tree.column('col3', width=92, anchor='center')
        self.tree.column('col4', width=92, anchor='center')
        self.tree.heading('col1', text='name')
        self.tree.heading('col2', text='port')
        self.tree.heading('col3', text='q_pkt')
        self.tree.heading('col4', text='r_pkt')
        self.tree.configure(yscrollcommand=self.ybar.set)
        self.tree.bind("<Double-1>", self.dbClick2ShowNode)


        self.ge_network()
        self.create_node()

        self.cv_topo.shohid = StringVar()
        self.cv_topo.shohid.set("show")


        self.button_quit = Button(self.fr_mid, style="Q.TButton",command=self.quit)

        self.button_refresh = Button(self.fr_mid, style="R.TButton", command=self.refresh_network)
        self.topo_xscroll = MyScrollbar(self.fr_topo, canvas = self.cv_topo, nodes = self.nodes, node_size = self.node_size, shohid=self.cv_topo.shohid.get(), orient="horizontal", command=self.cv_topo.xview)
        self.topo_yscroll = MyScrollbar(self.fr_topo, canvas = self.cv_topo, nodes = self.nodes, node_size = self.node_size, shohid=self.cv_topo.shohid.get(), orient="vertical", command=self.cv_topo.yview)
        self.cv_topo.configure(yscrollcommand=partial(self.topo_yscroll.set,node_size=self.node_size, shohid=self.cv_topo.shohid.get()), xscrollcommand=partial(self.topo_xscroll.set, node_size = self.node_size, shohid=self.cv_topo.shohid.get()))

        #self.cv.pack()
        self.cv_topo.bind('<Motion>' , self.move_handler)
        self.cv_topo.bind('<Button-1>', self.click_handler)

        self.button_InfShowHide = Button(self.fr_mid, textvariable=self.cv_topo.shohid, command=self.labelShowHide)

        self.edgeWarn_th = threading.Thread(target=self.edge_traffic_warn, args=(self.event,self.topology, self.cv_topo))
        self.edgeWarn_th.setDaemon(True)
        self.edgeWarn_th.start()
        
        self.v = StringVar()
        self.on_off_xpos = 150
        self.on_off_ypos = 500

        # self.rate_set = []
        # for text, mode in modes:
            # self.rate_set.append(Radiobutton(self.fr_mid, text=text, variable=self.v, value=mode, command=self.mitigation))
        #     self.on_off_ypos += 25

        self.rate_set = Checkbutton(self.fr_mid, text=modes[1], variable=self.v, onvalue="On", offvalue="Off", command=self.mitigation)
        self.typeSetting()

    def typeSetting(self):
        self.fr_bg.pack()
        self.fr_tp.pack(side="bottom")
        # self.fr_tb.pack(side="right")

        # self.L1.place(x=85, y=100)
        # self.thres.place(x=480, y=420)
        # self.thresIn.place(x=600, y=420)

        # self.button_InfShowHide.place(x=10, y=370)
        # self.enter.place(x=655, y=420)
        # self.button_quit.place(x=850, y=450)
        # self.button_refresh.place(x=850, y=400)

        self.L1.grid(row=0, column=0, pady=(0,20))
        self.thres.grid(row=1, column=0, sticky="W")
        self.thresIn.grid(row=1, column=0)
        self.enter.grid(row=1, column=0, sticky="E")
        self.zoomIn.grid(row=2, column=0)
        self.zoomOut.grid(row=3, column=0)
        self.button_InfShowHide.grid(row=4, column=0, pady=20)
        self.rate_set.grid(row=5, column=0)
        # self.rate_set[1].grid(row=6, column=0)

        self.button_refresh.grid(row=8, column = 0, pady=(30,0))
        self.button_quit.grid(row=9, column=0)

        self.topo_xscroll.pack(side="bottom", fill="x", ipady=0)
        self.topo_yscroll.pack(side="right", fill="y", ipadx=0)
        self.cv_topo.pack(expand="Yes", anchor="center", side="left")

        self.cv_tp.pack(expand="Yes", side="top", fill="both",ipadx=0,ipady=0,padx=0,pady=0)
        self.fr_topo.pack(expand="Yes", anchor="center",side="left", fill="both")
        self.fr_mid.pack(expand="Yes",side="left", anchor="center")
        self.fr_table.pack(expand="Yes", side="right",anchor="center",fill="both")

        self.cv_btm.pack(expand="Yes", side="bottom", fill="both")


    def initStyle(self):

        self.node_size = 10
        self.fonts = ("arial", 12)

        ####################  Color  ####################
        self.bg_tp = "black" 
        self.bg = "white"
        self.host_color = "white"
        self.sw_color = "white"
        self.r_color  = "#ffcc66"
        self.q_color  = "#B585BE"
        #self.ov_r_color = "red"
        #self.ov_q_color = "yellow"
        self.notice_color = "#5D5D5D"


        ####################   Img   ####################
        quitImage = Image.open('Img/up_quit.png').resize((180,42), Image.ANTIALIAS)
        refreshImage = Image.open('Img/up_refresh.png').resize((180,42), Image.ANTIALIAS)

        b_quitImage = Image.open('Img/down_quit.png').resize((180,42), Image.ANTIALIAS)
        b_refreshImage = Image.open('Img/down_refresh.png').resize((180,42), Image.ANTIALIAS)

        self.quitPhoto = ImageTk.PhotoImage(quitImage) 
        self.refreshPhoto = ImageTk.PhotoImage(refreshImage) 
        self.b_quitPhoto = ImageTk.PhotoImage(b_quitImage) 
        self.b_refreshPhoto = ImageTk.PhotoImage(b_refreshImage) 
        TBgImage = Image.open('Img/top_bg.png').resize((1100,100), Image.ANTIALIAS)
        BBgImage = Image.open('Img/bottom_bg.png').resize((1100,100), Image.ANTIALIAS)
        TopoBgImage = Image.open('Img/gray_bg.png').resize((400,400), Image.ANTIALIAS)

        self.t_bgPhoto = ImageTk.PhotoImage(TBgImage)
        self.b_bgPhoto = ImageTk.PhotoImage(BBgImage)
        self.topo_bgPhoto = ImageTk.PhotoImage(TopoBgImage)

        upzinImage = Image.open('Img/up_zoomin.png').resize((180,42), Image.ANTIALIAS)
        downzinImage = Image.open('Img/down_zoomin.png').resize((180,42), Image.ANTIALIAS)
        actzinImage = Image.open('Img/active_zoomin.png').resize((180,42), Image.ANTIALIAS)
        diszinImage = Image.open('Img/disable_zoomin.png').resize((180,42), Image.ANTIALIAS)

        self.upzinPhoto = ImageTk.PhotoImage(upzinImage) 
        self.downzinPhoto = ImageTk.PhotoImage(downzinImage) 
        self.actzinPhoto = ImageTk.PhotoImage(actzinImage) 
        self.diszinPhoto = ImageTk.PhotoImage(diszinImage) 

        upzoutImage = Image.open('Img/up_zoomout.png').resize((180,42), Image.ANTIALIAS)
        downzoutImage = Image.open('Img/down_zoomout.png').resize((180,42), Image.ANTIALIAS)
        actzoutImage = Image.open('Img/active_zoomout.png').resize((180,42), Image.ANTIALIAS)
        diszoutImage = Image.open('Img/disable_zoomout.png').resize((180,42), Image.ANTIALIAS)

        self.upzoutPhoto = ImageTk.PhotoImage(upzoutImage) 
        self.downzoutPhoto = ImageTk.PhotoImage(downzoutImage) 
        self.actzoutPhoto = ImageTk.PhotoImage(actzoutImage) 
        self.diszoutPhoto = ImageTk.PhotoImage(diszoutImage) 


        ####################  Style  ####################        
        self.style = Style()

        self.style.configure("TButton",
                font=self.fonts, relief="flat")

        self.style.map("TButton",
                background=[("active", "pink"), ("disabled", "#f0f0f0")],
                foreground=[("active", "white"), ("disabled", "white")]
                )
        self.style.map("Selected.TButton",
                background=[("active", "pink"), ("disabled", "#f0f0f0")],
                foreground=[("active", "white"), ("disabled", "white")]
                )

        self.style.configure("Q.TButton",
                background=self.bg, 
                font=self.fonts, relief="flat", 
                image = self.quitPhoto, padding=0,
                )
        self.style.map("Q.TButton",
                background=[("active",self.bg)],
                image=[("active",self.b_quitPhoto)],
                )

        self.style.configure("R.TButton",
                background=self.bg,
                image = self.refreshPhoto, padding=0)
        self.style.map("R.TButton",
                background=[("active",self.bg)],
                image=[("active",self.b_refreshPhoto)],
                )

        self.style.configure("zoom.TButton", background=self.bg, padding=0)
        self.style.map("zoom.TButton",
                background=[("active", self.bg), ("disabled", self.bg)])

        self.style.configure("in.zoom.TButton", image = self.upzinPhoto)
        self.style.map("in.zoom.TButton",
                image = [("active", self.actzinPhoto), ("disabled", self.diszinPhoto)])
        self.style.configure("S.in.zoom.TButton", image = self.downzinPhoto)

        
        self.style.configure("out.zoom.TButton", image = self.upzoutPhoto)
        self.style.map("out.zoom.TButton",
                image = [("active", self.actzoutPhoto), ("disabled", self.diszoutPhoto)])
        self.style.configure("S.out.zoom.TButton", image = self.downzoutPhoto)

        self.style.configure("TFrame",
                background = self.bg, 
                )
        self.style.configure("TLabel",
                background = self.bg, 
                )

    def ge_network(self):
        """ generate network """

        self.G = nx.Graph()
        pos = {}
        fixed = []
        connected_gw = []
        for port, node in self.event.node_links["s4"]:
            if node != "s5":
                connected_gw.append(node)

        myCos = lambda x: np.cos(np.deg2rad(x))
        mySin = lambda x: np.sin(np.deg2rad(x))
        for s, mac in sorted(self.sw_mac.items()):
            self.G.add_node(mac.encode('utf-8'))
            if s in connected_gw:
                pos[mac] = (0.2+1.1*myCos(90+15.0*connected_gw.index(s)), -1.4+connected_gw.index(s)*0.225)
                # pos[mac] = (-1, -1.2+connected_gw.index(s)*0.225)
                for port, node in self.event.node_links[s]:
                    if node[0] == 's':
                        pos[self.sw_mac[node]] = (-1.2,pos[mac][1])
                        fixed.append(self.sw_mac[node])
                        for p,n in self.event.node_links[node]:
                            if n[0] == 'h':
                                pos[self.h_mac[n]] = (-1.7, pos[mac][1])
                                fixed.append(self.h_mac[n])

                    elif node[0] == 'h':
                        pos[self.h_mac[node]] = (-1.7, pos[mac][1])
                        fixed.append(self.h_mac[node])
                fixed.append(mac)
           

        for h, mac in sorted(self.h_mac.items()):
            self.G.add_node(mac.encode('utf-8'))
            # pos[mac] = (0,int(h[1:])/15)
            # fixed.append(mac)

        edge = []
        for no, link in sorted(self.topology.items()):
            keys = link.keys()
            edge.append((keys[0],keys[1]))

        self.G.add_edges_from(edge)

        pos["00:00:00:04:15:00"] = (0.2,0)
        pos["00:00:00:05:15:00"] = (0.7,0)
        pos["00:00:00:00:03:03"] = (1.5,0.5)
        pos["00:00:00:00:02:02"] = (1.5,-0.5)
        pos["00:00:00:03:15:00"] = (1.1,0.25)
        pos["00:00:00:02:15:00"] = (1.1,-0.25)

        fixed.append("00:00:00:04:15:00")
        fixed.append("00:00:00:05:15:00")
        fixed.append("00:00:00:00:03:03")
        fixed.append("00:00:00:00:02:02")
        fixed.append("00:00:00:03:15:00")
        fixed.append("00:00:00:02:15:00")

        self.links = self.G.edges # [[mac1,mac2],[mac3,mac4],...]
        self.nodes = nx.spring_layout(self.G, pos=pos, fixed=fixed) # {mac1:[x1,y1], mac2:[x2, y2]}

    def refresh_network(self):
        """ refresh network """

        self.G.clear()
        self.cv_topo.delete("all")
        self.cv_topo.labelGw.destroy()
        self.cv_topo.labelRt.destroy()
        self.cv_topo.labelSv.destroy()
        self.cv_topo.labelVt.destroy()
        self.cv_topo.labelCt.destroy()
        self.event.cleanObjID()

        self.ge_network()
        self.cv_topo.create_image(0,0, image=self.topo_bgPhoto, anchor="nw")
        self.create_node()
        self.cv_topo.shohid.set("hide")

    def create_node(self):
        """ create node """

        for node, pos in self.nodes.items():
            pos[0] = (pos[0]+2)*100
            pos[1] = (pos[1]+2)*100

        for link in self.links:
            if self.event.getQR(link[0], link[1], 1) == 'q':
                # link[0] -> half : query
                No = self.cv_topo.create_line(
                        self.nodes[link[0]][0]+self.node_size/2, 
                        self.nodes[link[0]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2, 
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.q_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])
                # link[1] -> half : response
                No = self.cv_topo.create_line(
                        self.nodes[link[1]][0]+self.node_size/2,
                        self.nodes[link[1]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2,
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.r_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])
            elif self.event.getQR(link[0], link[1], 1) == 'r':
                # link[1] -> half : query
                No = self.cv_topo.create_line(
                        self.nodes[link[1]][0]+self.node_size/2,
                        self.nodes[link[1]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2,
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.q_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])
                # link[0] -> half : response
                No = self.cv_topo.create_line(
                        self.nodes[link[0]][0]+self.node_size/2,
                        self.nodes[link[0]][1]+self.node_size/2,
                        (self.nodes[link[0]][0]+self.nodes[link[1]][0]+self.node_size)/2,
                        (self.nodes[link[0]][1]+self.nodes[link[1]][1]+self.node_size)/2,
                        fill=self.r_color, arrow=LAST, width=2)
                self.event.putObjID(No, link[0], link[1])

        self.switches = {}
        self.hosts = {}
        for node, pos in self.nodes.items():
            if node[15:] == "00" :
                # sw = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_sw)
                sw = self.cv_topo.create_oval(pos[0], pos[1], pos[0]+self.node_size, pos[1]+self.node_size, fill=self.sw_color)
                self.switches[node] = sw
                if node[0:] == "00:00:00:04:15:00":
                    self.cv_topo.labelGw = Label(self.cv_topo, text="Gateway\n Switch", width=8, foreground="white", background="black", borderwidth=0, anchor="center", font=("arial", 10))
                    self.cv_topo.labelGw.place(x=pos[0] , y=pos[1]+self.node_size)
                    self.controller = self.cv_topo.create_polygon(
                            pos[0]+6*self.node_size, 10*self.node_size+pos[1],
                            pos[0]+7*self.node_size, 10*self.node_size+pos[1],
                            pos[0]+7.5*self.node_size, 10*self.node_size+pos[1]+sqrt(3)*self.node_size/2,
                            pos[0]+7*self.node_size, 10*self.node_size+pos[1]+sqrt(3)*self.node_size,
                            pos[0]+6*self.node_size, 10*self.node_size+pos[1]+sqrt(3)*self.node_size,
                            pos[0]+5.5*self.node_size, 10*self.node_size+pos[1]+sqrt(3)*self.node_size/2, fill="white", outline="black")
                    self.cv_topo.labelCt = Label(self.cv_topo, text="Controller", width=8, foreground="white", background="black", borderwidth=0, anchor="center", font=("arial", 10))
                    self.cv_topo.labelCt.place(x=pos[0]+6*self.node_size, y=10*self.node_size+pos[1]+sqrt(3)*self.node_size)
                if node[0:] == "00:00:00:05:15:00":
                    self.cv_topo.labelRt = Label(self.cv_topo, text="Router", width=7, foreground="white", background="black", borderwidth=0, anchor="center", font=("arial", 10))
                    self.cv_topo.labelRt.place(x=pos[0] , y=pos[1]+self.node_size)


            else:
                host = self.cv_topo.create_rectangle(pos[0], pos[1], pos[0]+self.node_size, pos[1]+self.node_size, fill=self.host_color, outline="black")
                # host = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_host)
                self.hosts[node] = host
                if node[0:] == "00:00:00:00:03:03":
                    self.cv_topo.labelSv = Label(self.cv_topo, text=" DNS\nServer", width=7, foreground="white", background="black", borderwidth=0, anchor="center", font=("arial", 10))
                    self.cv_topo.labelSv.place(x=pos[0] , y=pos[1]+self.node_size)
                if node[0:] == "00:00:00:00:01:01":
                    self.cv_topo.labelVt = Label(self.cv_topo, text="Victim", width=7, foreground="white", background="black", borderwidth=0, anchor="center", font=("arial", 10))
                    self.cv_topo.labelVt.place(x=pos[0] , y=pos[1]+self.node_size)

        self.overlaplist = []
        self.comparelist = []
        for no, link in sorted(self.topology.items()):
            mac1 = link.keys()[0]
            mac2 = link.keys()[1]
            self.overlaplist.append(self.event.getObjID(mac1, mac2)[0])
            self.overlaplist.append(self.event.getObjID(mac1, mac2)[1])

        self.comparelist = self.overlaplist
        for Id in self.overlaplist:
            flag = 0
            if self.comparelist == None:
                break
            del self.comparelist[self.comparelist.index(Id)]
            x1, y1, x2, y2 = self.cv_topo.coords(Id)
            result = self.cv_topo.find_overlapping(x1, y1, x2, y2)
            for x in self.comparelist:
                x_pos = self.cv_topo.coords(x)
                if x_pos in result:
                    self.refresh_network()
                    flag = 1
                    break
            if flag == 1:
                break


    def edge_traffic_warn(self, event, topology, cv_topo):
        """ detect which edge is busy, warn user via color changing """
        while event.is_set() is True:
            pktMax = 0
            edgeWidth_q = 2
            edgeWidth_r = 2
            for no, link in sorted(topology.items()):
                mac1 = link.keys()[0]
                mac2 = link.keys()[1]
                pktNum_q = event.getPktNum(mac1, mac2, 'q')
                pktNum_r = event.getPktNum(mac1, mac2, 'r')
                pktMax = pktNum_q if pktNum_q > pktMax else pktMax
                pktMax = pktNum_r if pktNum_r > pktMax else pktMax
                pktMax = 20 if pktMax < 20 else pktMax

                if pktNum_q <= qpktThreshold:
                    edgeWidth_q = (pktNum_q%5)+2
                    edgeWidth_q = 2 if edgeWidth_q < 2 else edgeWidth_q
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[0], fill=self.q_color, width=edgeWidth_q)
                elif pktNum_q > qpktThreshold:
                    edgeWidth_q = int(pktNum_q*20/pktMax)
                    edgeWidth_q = 7 if edgeWidth_q < 7 else edgeWidth_q
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[0], fill=self.edgeColorCtr(self.q_color, edgeWidth_q, "q"), width=edgeWidth_q)
                if pktNum_r <= rpktThreshold:
                    edgeWidth_r = (pktNum_r%5)+2
                    edgeWidth_r = 2 if edgeWidth_r < 2 else edgeWidth_r
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[1], fill=self.r_color, width=edgeWidth_r)
                elif pktNum_r > rpktThreshold:
                    edgeWidth_r = int(pktNum_r*20/pktMax)
                    edgeWidth_r = 7 if edgeWidth_r < 7 else edgeWidth_r
                    cv_topo.itemconfig(event.getObjID(mac1, mac2)[1], fill=self.edgeColorCtr(self.r_color, edgeWidth_r, "r"), width=edgeWidth_r)

            for i in range(0, 10):
                if event.is_set() is False:
                    break
                sleep(1)

    def edgeColorCtr(self, color, width, pkttype="q"):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        if pkttype == "q":
            while width > 6:
                g -= 15
                width -= 2
        elif pkttype == "r":
            while width > 6:
                g -= 10
                b -= 10
                width -= 2
        return "#{0:02x}{1:02x}{2:02x}".format(r,g,b)

    def mitigation(self):
        if self.v.get() == "On":
            self.event.setMeterFlag(1)
            self.rate_set.configure(text=modes[0])
            print "Mitigation is opened"
        elif self.v.get() == "Off":
            self.event.setMeterFlag(0)
            self.rate_set.configure(text=modes[1])
            print "Mitigation is closed"

    def dbClick2ShowNode(self, event):
        """ click one row to show node position """
        for s_mac, pos in self.switches.items():
            self.cv_topo.itemconfig(self.switches[s_mac], fill=self.sw_color)
        for h_mac, pos in self.hosts.items():
            self.cv_topo.itemconfig(self.hosts[h_mac], fill=self.host_color)
        name = self.tree.item(self.tree.selection())['values'][0]
        if name == "DNS Server":
            name = "h3"
        elif name == "victim":
            name = "h1"
        elif name == "gateway sw":
            name = "s4"
        elif name == "router":
            name = "s5"
        mac = self.event.name2mac(name)
        if mac[15:] == "00":
            self.cv_topo.itemconfig(self.switches[mac], fill=self.notice_color)
        else:
            self.cv_topo.itemconfig(self.hosts[mac], fill=self.notice_color)

    def quit(self):
        #TODO clear others 
        self.G.clear()
        self.cv_topo.delete("all")
        #self.cv.delete("all")
        self.root.destroy()
        self.event.clear()
        # exit()

    def move_handler(self, event):
        """ detect if mouse is focus, show information """
        self.var.set('')
        
        for node, pos in self.nodes.items():
            if  pos[0] < event.x < pos[0]+self.node_size and pos[1] < event.y < pos[1]+self.node_size:
                name = self.event.mac2name(node)
                if node[15:] == "00" :
                    self.var.set(name+" : "+node)
                else:
                    self.var.set(name+" : "+node)
                break

    def click_handler(self, event):
        """ click one node to show information """
        if self.tree != None:
            self.tree.pack_forget()
            self.ybar.pack_forget()
            x = self.tree.get_children()
            for item in x:
                self.tree.delete(item)
        for node, pos in self.nodes.items():
            if  pos[0] < event.x < pos[0]+self.node_size and pos[1] < event.y < pos[1]+self.node_size:
                for s_mac, pos in self.switches.items():
                    self.cv_topo.itemconfig(self.switches[s_mac], fill=self.sw_color)
                for h_mac, pos in self.hosts.items():
                    self.cv_topo.itemconfig(self.hosts[h_mac], fill=self.host_color)
                # self.tree = Treeview(self.fr_table, columns=('col1', 'col2', 'col3', 'col4') ,show='headings')

                inf = self.event.getNodeInf(node)

                for i in inf:
                   self.tree.insert('', 'end', values=i)

                # self.tree.place(x=480, y=170)
                # self.ybar.place(x=800, y=170, height=218)
                self.tree.pack(side="left", fill='both', pady=60)
                self.ybar.pack(side="left", fill='y', pady=60)


    def getThreshold(self):
        try:
            int(self.usrIn.get())
        except ValueError:
            self.usrIn.set("")
            messagebox.showerror("Error", "You enter the wrong type !!\nPlease enter a number with type \"int\"")
        else:
            if 0 <= int(self.usrIn.get()) <= 1000:
                self.event.thr_res_num = int(self.usrIn.get())
                qpktThreshold = self.usrIn.get()
                rpktThreshold = self.usrIn.get()
                print "You change the threshold to " + str(self.event.thr_res_num)
            else:
                self.usrIn.set("")
                messagebox.showwarning("Warning", "Please enter a number which value is between 0 to 1000 (both includiing) !!")

    def labelShowHide(self):
        if self.cv_topo.shohid.get() == "show":
            x0 = self.cv_topo.canvasx(0)
            y0 = self.cv_topo.canvasy(0)
            for node, pos in self.nodes.items():
                wx = pos[0] - x0
                wy = pos[1] - y0
                if node[15:] == "00" :
                    if node[0:] == "00:00:00:04:15:00":
                        self.cv_topo.labelGw.place(x=wx , y=wy+self.node_size)
                        self.cv_topo.labelCt.place(x=wx+6*self.node_size, y=10*self.node_size+wy+sqrt(3)*self.node_size)
                    if node[0:] == "00:00:00:05:15:00":
                        self.cv_topo.labelRt.place(x=wx , y=wy+self.node_size)
                else:
                    if node[0:] == "00:00:00:00:03:03":
                        self.cv_topo.labelSv.place(x=wx , y=wy+self.node_size)
                    if node[0:] == "00:00:00:00:01:01":
                        self.cv_topo.labelVt.place(x=wx , y=wy+self.node_size)
            self.cv_topo.shohid.set("hide")
        elif self.cv_topo.shohid.get() == "hide":
            self.cv_topo.labelGw.place_forget()
            self.cv_topo.labelRt.place_forget()
            self.cv_topo.labelSv.place_forget()
            self.cv_topo.labelVt.place_forget()
            self.cv_topo.labelCt.place_forget()
            self.cv_topo.shohid.set("show")

    def zoomRecord(self, event):
        self.zoom.x1 = self.cv_topo.canvasx(event.x)
        self.zoom.y1 = self.cv_topo.canvasy(event.y)

    def zoomCreate(self, event):
        self.cv_topo.delete(self.zoom.rect)
        self.zoom.x2 = self.cv_topo.canvasx(event.x)
        self.zoom.y2 = self.cv_topo.canvasy(event.y)
        self.zoom.rect = self.cv_topo.create_rectangle(self.zoom.x1, self.zoom.y1, self.zoom.x2, self.zoom.y2)
        self.zoom.area = abs(self.zoom.x2-self.zoom.x1)*abs(self.zoom.y2-self.zoom.y1)

    

    def zoomRelease(self, event=None, InOut="in"):
        
        op = "*" if InOut=="in" else "/"
        if self.zoom.area < 1:
            self.zoom.area = 1

        mag = sqrt((400*400)/self.zoom.area)
        if mag >= 8:
            mag = 8
        elif mag >= 4:
            mag = 4
        elif mag >= 2:
            mag = 2
        elif mag >= 0:
            mag = 1.5

        self.zoom.width = eval("self.zoom.width "+op+"mag")
        self.zoom.height= eval("self.zoom.height"+op+"mag")
        if fr_topo_width-50 < self.zoom.width < fr_topo_width+50:
            self.zoom.width = fr_topo_width
            self.zoom.height = fr_topo_height

        self.cv_topo.configure(scrollregion=(0,0,self.zoom.width,self.zoom.height))
        self.cv_topo.yview_moveto(eval("self.zoom.y1"+op+"mag")/self.zoom.height)
        self.cv_topo.xview_moveto(eval("self.zoom.x1"+op+"mag")/self.zoom.width)

        self.node_size = eval("self.node_size "+op+" mag")
        for node, pos in self.nodes.items():
            self.nodes[node] = [eval("pos[0] "+op+" mag"), eval("pos[1] "+op+" mag")]

        result = self.cv_topo.find_overlapping(0, 0, 10000, 10000)
        for Id in result:
            ords = self.cv_topo.coords(Id)
            z = [eval("o"+op+"mag") for o in ords]
            if len(ords) == 4:
                self.cv_topo.coords(Id, z[0], z[1], z[2], z[3])
            if len(ords) == 12:
                self.cv_topo.coords(Id,
                        z[0], z[1], z[2], z[3],
                        z[4], z[5], z[6], z[7],
                        z[8], z[9], z[10], z[11])
        self.labelShowHide()
        self.labelShowHide()
        #self.shohid.set("hide")
        self.cv_topo.delete(self.zoom.rect)
        self.cv_topo.configure(
                yscrollcommand= partial(self.topo_yscroll.set, nodes=self.nodes, node_size=self.node_size),
                xscrollcommand= partial(self.topo_xscroll.set, nodes=self.nodes, node_size = self.node_size))

        tmp = self.zoomState
        if self.zoom.width * 8 > 10000 and self.zoomState == "in":
            self.zoomIn.state(["disabled"])
        elif self.zoom.width / 8 <  50 and self.zoomState == "out":
            self.zoomOut.state(["disabled"])
        else:
            self.zoomIn.state(["!disabled"])
            self.zoomOut.state(["!disabled"])
            self.zoomState = "Not"
            
        self.topoZoom(InOut=tmp)

    def topoZoom(self, InOut="in"):
        self.cv_topo.unbind("<Button-1>")
        self.cv_topo.unbind("<B1-Motion>")
        self.cv_topo.unbind("<ButtonRelease-1>")


        if self.zoomState == InOut:
            self.zoomIn.configure(style="in.zoom.TButton")
            self.zoomOut.configure(style="out.zoom.TButton")

            self.zoomState = "Not"
            self.cv_topo.bind('<Motion>' , self.move_handler)
            self.cv_topo.bind('<Button-1>', self.click_handler)
        else: # self.zoomState = "Not"
            if InOut == "in":
                self.zoomIn.configure(style="S.in.zoom.TButton")
                self.zoomOut.configure(style="out.zoom.TButton")
            elif InOut == "out":
                self.zoomIn.configure(style="in.zoom.TButton")
                self.zoomOut.configure(style="S.out.zoom.TButton")

            self.zoomState = InOut
            self.cv_topo.bind("<Button-1>", self.zoomRecord)
            self.cv_topo.bind("<B1-Motion>", self.zoomCreate)
            self.cv_topo.bind("<ButtonRelease-1>", partial(self.zoomRelease,InOut=InOut))



def main():

    sw_mac = {'s16': '00:00:00:10:15:00', 's9': '00:00:00:09:15:00', 's8': '00:00:00:08:15:00', 's17': '00:00:00:11:15:00', 's3': '00:00:00:03:15:00', 's2': '00:00:00:02:15:00', 's1': '00:00:00:01:15:00', 's10': '00:00:00:0a:15:00', 's7': '00:00:00:07:15:00', 's6': '00:00:00:06:15:00', 's5': '00:00:00:05:15:00', 's4': '00:00:00:04:15:00', 's13': '00:00:00:0d:15:00', 's20': '00:00:00:14:15:00', 's18': '00:00:00:12:15:00', 's15': '00:00:00:0f:15:00', 's12': '00:00:00:0c:15:00', 's19': '00:00:00:13:15:00', 's21': '00:00:00:15:15:00', 's14': '00:00:00:0e:15:00', 's11': '00:00:00:0b:15:00'}
    
    h_mac = {u'h8': u'00:00:00:00:0c:08', u'h9': u'00:00:00:00:0d:09', u'h7': u'00:00:00:00:0b:07', u'h1': u'00:00:00:00:01:01', u'h6': u'00:00:00:00:0a:06', u'h12': u'00:00:00:00:10:0c', u'h13': u'00:00:00:00:12:0d', u'h14': u'00:00:00:00:13:0e', u'h15': u'00:00:00:00:15:0f', u'h4': u'00:00:00:00:07:04', u'h5': u'00:00:00:00:08:05', u'h10': u'00:00:00:00:0e:0a', u'h2': u'00:00:00:00:02:02', u'h11': u'00:00:00:00:0f:0b', u'h3': u'00:00:00:00:03:03'}
    topology = {'24': {'00:00:00:05:15:00': 3, '00:00:00:04:15:00': 10}, '25': {'00:00:00:0d:15:00': 2, '00:00:00:04:15:00': 3}, '26': {'00:00:00:0e:15:00': 2, '00:00:00:04:15:00': 4}, '27': {'00:00:00:11:15:00': 2, '00:00:00:04:15:00': 7}, '20': {'00:00:00:07:15:00': 2, '00:00:00:04:15:00': 12}, '21': {'00:00:00:06:15:00': 2, '00:00:00:04:15:00': 11}, '22': {'00:00:00:08:15:00': 2, '00:00:00:04:15:00': 13}, '23': {'00:00:00:09:15:00': 2, '00:00:00:04:15:00': 14}, '28': {'00:00:00:0f:15:00': 2, '00:00:00:04:15:00': 5}, '29': {'00:00:00:04:15:00': 9, '00:00:00:14:15:00': 2}, '1': {u'00:00:00:00:12:0d': 1, '00:00:00:12:15:00': 1}, '0': {'00:00:00:13:15:00': 1, u'00:00:00:00:13:0e': 1}, '3': {'00:00:00:0d:15:00': 1, u'00:00:00:00:0d:09': 1}, '2': {'00:00:00:08:15:00': 1, u'00:00:00:00:08:05': 1}, '5': {'00:00:00:01:15:00': 1, u'00:00:00:00:01:01': 1}, '4': {u'00:00:00:00:0c:08': 1, '00:00:00:0c:15:00': 1}, '7': {'00:00:00:07:15:00': 1, u'00:00:00:00:07:04': 1}, '6': {'00:00:00:0a:15:00': 1, u'00:00:00:00:0a:06': 1}, '9': {u'00:00:00:00:0f:0b': 1, '00:00:00:0f:15:00': 1}, '8': {u'00:00:00:00:10:0c': 1, '00:00:00:10:15:00': 1}, '11': {u'00:00:00:00:03:03': 1, '00:00:00:03:15:00': 1}, '10': {'00:00:00:0e:15:00': 1, u'00:00:00:00:0e:0a': 1}, '13': {u'00:00:00:00:02:02': 1, '00:00:00:02:15:00': 1}, '12': {u'00:00:00:00:15:0f': 1, '00:00:00:15:15:00': 1}, '15': {'00:00:00:01:15:00': 2, '00:00:00:06:15:00': 1}, '14': {u'00:00:00:00:0b:07': 1, '00:00:00:0b:15:00': 1}, '17': {'00:00:00:05:15:00': 2, '00:00:00:03:15:00': 2}, '16': {'00:00:00:05:15:00': 1, '00:00:00:02:15:00': 2}, '19': {'00:00:00:04:15:00': 1, '00:00:00:0b:15:00': 2}, '18': {'00:00:00:04:15:00': 2, '00:00:00:0c:15:00': 2}, '31': {'00:00:00:13:15:00': 2, '00:00:00:04:15:00': 8}, '30': {'00:00:00:10:15:00': 2, '00:00:00:04:15:00': 6}, '34': {'00:00:00:14:15:00': 1, '00:00:00:15:15:00': 2}, '33': {'00:00:00:11:15:00': 1, '00:00:00:12:15:00': 2}, '32': {'00:00:00:0a:15:00': 2, '00:00:00:09:15:00': 1}}
    direction = {'24': {'00:00:00:05:15:00': 'r', '00:00:00:04:15:00': 'q'}, '25': {'00:00:00:0d:15:00': 'q', '00:00:00:04:15:00': 'r'}, '26': {'00:00:00:0e:15:00': 'q', '00:00:00:04:15:00': 'r'}, '27': {'00:00:00:11:15:00': 'q', '00:00:00:04:15:00': 'r'}, '20': {'00:00:00:07:15:00': 'q', '00:00:00:04:15:00': 'r'}, '21': {'00:00:00:06:15:00': 'q', '00:00:00:04:15:00': 'r'}, '22': {'00:00:00:08:15:00': 'q', '00:00:00:04:15:00': 'r'}, '23': {'00:00:00:09:15:00': 'q', '00:00:00:04:15:00': 'r'}, '28': {'00:00:00:0f:15:00': 'q', '00:00:00:04:15:00': 'r'}, '29': {'00:00:00:04:15:00': 'r', '00:00:00:14:15:00': 'q'}, '1': {'00:00:00:12:15:00': 'r', u'00:00:00:00:12:0d': 'q'}, '0': {'00:00:00:13:15:00': 'r', u'00:00:00:00:13:0e': 'q'}, '3': {'00:00:00:0d:15:00': 'r', u'00:00:00:00:0d:09': 'q'}, '2': {'00:00:00:08:15:00': 'r', u'00:00:00:00:08:05': 'q'}, '5': {'00:00:00:01:15:00': 'r', u'00:00:00:00:01:01': 'q'}, '4': {u'00:00:00:00:0c:08': 'q', '00:00:00:0c:15:00': 'r'}, '7': {'00:00:00:07:15:00': 'r', u'00:00:00:00:07:04': 'q'}, '6': {'00:00:00:0a:15:00': 'r', u'00:00:00:00:0a:06': 'q'}, '9': {u'00:00:00:00:0f:0b': 'q', '00:00:00:0f:15:00': 'r'}, '8': {u'00:00:00:00:10:0c': 'q', '00:00:00:10:15:00': 'r'}, '11': {u'00:00:00:00:03:03': 'r', '00:00:00:03:15:00': 'q'}, '10': {'00:00:00:0e:15:00': 'r', u'00:00:00:00:0e:0a': 'q'}, '13': {'00:00:00:02:15:00': 'r', u'00:00:00:00:02:02': 'q'}, '12': {'00:00:00:15:15:00': 'r', u'00:00:00:00:15:0f': 'q'}, '15': {'00:00:00:01:15:00': 'q', '00:00:00:06:15:00': 'r'}, '14': {u'00:00:00:00:0b:07': 'q', '00:00:00:0b:15:00': 'r'}, '17': {'00:00:00:05:15:00': 'q', '00:00:00:03:15:00': 'r'}, '16': {'00:00:00:05:15:00': 'r', '00:00:00:02:15:00': 'q'}, '19': {'00:00:00:04:15:00': 'r', '00:00:00:0b:15:00': 'q'}, '18': {'00:00:00:04:15:00': 'r', '00:00:00:0c:15:00': 'q'}, '31': {'00:00:00:13:15:00': 'q', '00:00:00:04:15:00': 'r'}, '30': {'00:00:00:10:15:00': 'q', '00:00:00:04:15:00': 'r'}, '34': {'00:00:00:14:15:00': 'r', '00:00:00:15:15:00': 'q'}, '33': {'00:00:00:11:15:00': 'r', '00:00:00:12:15:00': 'q'}, '32': {'00:00:00:0a:15:00': 'q', '00:00:00:09:15:00': 'r'}}
    node_links = {u'h8': [[1, 's12']], u'h9': [[1, 's13']], u'h2': [[1, 's2']], u'h3': [[1, 's3']], u'h1': [[1, 's1']], u'h6': [[1, 's10']], u'h7': [[1, 's11']], u'h4': [[1, 's7']], u'h5': [[1, 's8']], 's9': [[2, 's4'], [1, 's10']], 's8': [[2, 's4'], [1, u'h5']], 's3': [[1, u'h3'], [2, 's5']], 's2': [[1, u'h2'], [2, 's5']], 's1': [[1, u'h1'], [2, 's6']], 's7': [[2, 's4'], [1, u'h4']], 's6': [[1, 's1'], [2, 's4']], 's5': [[2, 's3'], [1, 's2'], [3, 's4']], 's4': [[2, 's12'], [3, 's13'], [5, 's15'], [4, 's14'], [12, 's7'], [13, 's8'], [14, 's9'], [1, 's11'], [6, 's16'], [7, 's17'], [10, 's5'], [11, 's6'], [9, 's20'], [8, 's19']], 's19': [[1, u'h14'], [2, 's4']], 's18': [[1, u'h13'], [2, 's17']], 's13': [[2, 's4'], [1, u'h9']], 's12': [[2, 's4'], [1, u'h8']], 's11': [[2, 's4'], [1, u'h7']], 's10': [[1, u'h6'], [2, 's9']], 's17': [[2, 's4'], [1, 's18']], 's16': [[2, 's4'], [1, u'h12']], 's15': [[2, 's4'], [1, u'h11']], 's14': [[2, 's4'], [1, u'h10']], u'h10': [[1, 's14']], u'h11': [[1, 's15']], u'h12': [[1, 's16']], u'h13': [[1, 's18']], u'h14': [[1, 's19']], u'h15': [[1, 's21']], 's20': [[2, 's4'], [1, 's21']], 's21': [[1, u'h15'], [2, 's20']]}
    event = myEvent(topology, direction, node_links)
    event.recordName(h_mac, sw_mac)
    c = ControllerGui(event, sw_mac, h_mac, topology)
    c.root.mainloop()
if __name__ == '__main__':
    main()
