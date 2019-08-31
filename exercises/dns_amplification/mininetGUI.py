import re
from time import sleep
from threading import Thread
from functools import partial

from Tkinter import *
from ttk import *
from Tkinter import Scale
from PIL import Image, ImageTk
import tkMessageBox as messagebox

from mininet.log import setLogLevel
from mininet.topolib import TreeNet
from mininet.examples.consoles import Graph

import mycontroller 
from event import myEvent
from Object import Object


class Console( Frame ):
    "A simple console on a host"
    
    def __init__( self, parent, net, node, height=300, width=300, title='Node'):
        """ init """
        Frame.__init__( self, parent, height=height, width=width-10)
        
        self.net = net
        self.node = node
        self.prompt = node.name + '# '
        self.height, self.width, self.title = height, width-10, title

        self.textStyle = {
            'font' : 'Mono 12',
            'bg': 'white',
            'fg': 'black',
            'width': 32,
            'height': 16,
            'highlightcolor': 'red',
            'selectforeground': 'black',
            'selectbackground': 'green'
        }

        self.text = self.makeWidgets()
        self.bindEvents()
        self.sendCmd( 'export TERM=dumb')

        self.outputHook = None

    def makeWidgets(self):
        """ Make a text area, and a scroll bar """
        display = Text(self, wrap='word', **self.textStyle)
        ybar = Scrollbar(self, orient='vertical',
                         command=display.yview )
        display.configure(yscrollcommand=ybar.set)
        display.pack(side='left', expand=True, fill='both')
        ybar.pack(side='right', fill = 'y')
        return display

    def bindEvents(self):
        self.text.bind( '<Return>', self.handleReturn)
        self.text.bind( '<Control-c>', self.handleInt)
        self.text.bind( '<KeyPress>', self.handleKey)
        self.tk.createfilehandler(self.node.stdout, READABLE,
                                  self.handleReadable)


    # ignoreChars = re.compile(r'[\x00-\x07\x09\x0b\x0c\x0e-\1f]+')
    # ignoreChars = re.compile(r'[\x00-\1f]+')

    def append(self, text):
        # text = self.ignoreChars.sub('',text)
        self.text.insert('end', text)
        self.text.mark_set('insert', 'end')
        self.text.see('insert')
        outputHook = lambda x, y: True
        if self.outputHook:
            outputHook = self.ouptuHook
        outputHook(self, text)
        
    def handleKey(self, event):
        char = event.char
        if self.node.waiting:
            self.node.write(char)

    def handleReturn(self, event):
        cmd = self.text.get('insert linestart', 'insert lineend')

        if self.node.waiting:
            self.node.write(event.char)
            return
        pos = cmd.find(self.prompt)
        if pos >= 0:
            cmd = cmd[ pos + len(self.prompt): ]
        self.sendCmd(cmd)

    def sendCmd(self, cmd):
        sleep(0.1)
        if not self.node.waiting:
            self.node.sendCmd(cmd)

    def handleInt(self, _event=None):
        "Handle control-c."
        self.node.sendInt()

    def handleReadable(self, _fds, timeoutms=None):
        "Handle file readable event."
        data = self.node.monitor(timeoutms)
        self.append(data)
        if not self.node.waiting:
            # self.append(self.prompt)
            None

    def waiting(self):
        return self.node.waiting

    def waitOutput(self):
        while self.node.waiting:
            self.handleReadable(self,timeoutms=1000)
            self.update()
    
    def clear(self):
        self.text.delete('1.0','end')
    

class MainConsole( Frame, object):
    " Console for Mininet. "

    menuStyle = { 'font': 'Geneva 12 bold'}

    def __init__( self, net, parent = None, width = 800, height=400):
        self.height = height
        self.width = width
        super(MainConsole, self).__init__(parent, height=self.height, width=self.width)
        # self.top = self.winfo_toplevel()
        # self.top.title( 'Mininet' )
        # self.top.geometry(str(self.width)+'x'+str(self.height))

        self.net = net

        self.initStyle()

        self.menu_fr = Frame(self, height=self.menu_height, width=800)
        self.cv = Canvas(self.menu_fr, height=self.menu_height, width = 800, highlightthickness=0)
        self.cv.create_image(0,0,image=self.bgPhoto, anchor=NW)

        self.menubar = self.createMenuBar("menu")
        self.level2bar = self.createMenuBar(None)
        self.level3bar = self.createMenuBar(None)

        self.createCframe()
        self.controller_th = None
        self.event = myEvent()
        

        self.hostCount = len(self.net.hosts)

        self.menu_fr.pack(expand=True, fill='both')
        self.cv.pack(expand=True, fill='both')
        self.cframe.pack( fill="both", anchor=NW)
        self.pack(expand=True, fill='both')

    def initStyle(self):

        self.fonts = ("arial", 12)
        
        self.cframe_height = 280
        self.menu_height = 120

        ##############  Img  ##############
        bgImage = Image.open('Img/top_bg.png').resize((800, self.menu_height), Image.ANTIALIAS)
        self.bgPhoto = ImageTk.PhotoImage(bgImage)

        ############## Style ##############
        self.style = Style()
        self.style.configure("TFrame",
                background="white",
                padding=0
                )
        # self.style.configure("Menubar.TFrame",
                # background="white",
                # )
        self.style.configure("Attack.TFrame",
                background="white",
                # padding=0
                )
        self.style.configure("TLabel",
                font = self.fonts,
                background="white"
                )

        self.style.configure("TCheckbutton",
                font = self.fonts,
                background="white"
                )
        self.style.configure("TButton",
                font = self.fonts,
                background="white"
                )
        
        self.style.configure("Selected.TButton",
                background="red",
                foreground="white"
                )
        self.style.map("Selected.TButton",
                background=[("active", "pink")],
                foreground=[("active", "white")]
                )

        self.style.map("UnSelected.TButton",
                background=[("active", "pink")],
                foreground=[("active", "white")]
                )

    def createConsoles(self, parent, nodes, title):
        "Create a grid of consoles in a frame."
        for node in nodes:
            self.consoles[node.name] = Console(parent, self.net, node, width=self.width/2, title = title)
        

    def createCframe(self):
        "Create a child frame."
        self.cframe = Frame(self, height=self.cframe_height, width=self.width)
        
        ############ Hosts -  View  - consoles ############
        self.consoles = {}
        titles = {
            'hosts': 'Host',
            'switches': 'Switch'
        }
        for name in titles:
            nodes = getattr(self.net, name)
            self.createConsoles( self.cframe, nodes, titles[name] )
        self.selected = [None, None]

        ############ Hosts - Function - Attack ############
        self.attack_frame = Frame(self.cframe, style="Attack.TFrame", height=self.cframe_height)

        host_list = [h.name for h in self.net.hosts]
        host_list.remove('h3')

        self.attack_frame.v_label = Label(self.attack_frame, text="Choose a victim: ")
        self.attack_frame.v_combo = Combobox(self.attack_frame, values=host_list, width=6)
        self.attack_frame.v_combo.current(0)
        self.attack_frame.v_combo.bind("<<ComboboxSelected>>", self.normal)
        
        self.attack_frame.a_label = Label(self.attack_frame, text="Choose attacker:")#, width=15)
        self.attack_frame.a_num_label = Label(self.attack_frame, text="num")#, width=15)
        self.attack_frame.a_num_combo = Combobox(self.attack_frame, values=range(1, 6), width=5)
        self.attack_frame.a_num_combo.current(0)
        self.attack_frame.a_num_combo.bind("<<ComboboxSelected>>", partial(self.changeAttackerNum, host_list = host_list))
        
        self.attacker = []
        self.attack_frame.a_name_label = Label(self.attack_frame, text="name")#, width=10)
        self.changeAttackerNum(event=None, host_list = host_list)
       
        self.attack_frame.i_label = Label(self.attack_frame, text="attack interval\n(second)", justify="center")
        self.attack_frame.p_num_label = Label(self.attack_frame, text="num of\nattack packets", justify="center")

        self.attack_frame.acpt_btn = Button(self.attack_frame, text="Accept", command=partial(self.acceptAttack, self.attack_frame.v_combo), width=10)
        
        block = [Label(self.attack_frame, text="\n  ",width=4 ) for i in range(0,15)]

        block[0].grid(row=1, column=0)
        block[1].grid(row=3, column=7)
        block[2].grid(row=4, column=4)
        block[3].grid(row=5, column=7)
        block[4].grid(row=6, column=7)
        block[5].grid(row=7, column=7)

        self.attack_frame.v_label.      grid(row=1, column=1)
        self.attack_frame.v_combo.      grid(row=2, column=1)
        self.attack_frame.a_label.      grid(row=1, column=2)
        self.attack_frame.a_num_label.  grid(row=2, column=2)
        self.attack_frame.a_num_combo.  grid(row=3, column=2)
        self.attack_frame.a_name_label. grid(row=2, column=3)
        self.attack_frame.i_label.      grid(row=2, column=5, columnspan=2)
        self.attack_frame.p_num_label.  grid(row=2,column=8)
        self.attack_frame.acpt_btn.     grid(row=8, column=9)
        
    
        ############ Hosts - Function - Normal ############
        self.normal_frame = Frame(self.cframe, style="TFrame", height=self.cframe_height)
        self.normal_frame.h_label = Label(self.normal_frame, text="Victim")
        self.normal_frame.v_label = Label(self.normal_frame, text=self.attack_frame.v_combo.get())
        self.normal_frame.i_label = Label(self.normal_frame, text="Interval (second) ", justify="center")
        self.normal_frame.r_var = IntVar()
        self.normal_frame.w_scale = Scale(self.normal_frame, from_=0.04, to=1,orient=HORIZONTAL,resolution=0.01, background="white")
        self.normal_frame.w_scale.set(0.3)
        self.normal_frame.r_cb = Checkbutton(self.normal_frame, text="random", variable=self.normal_frame.r_var,onvalue=1, offvalue=0)
        self.normal_frame.n_label = Label(self.normal_frame, text="num of normal packets")
        self.normal_frame.t_var = IntVar()
        self.normal_frame.t_var.set(500)
        self.normal_frame.n_entry = Entry(self.normal_frame, textvariable=self.normal_frame.t_var, width=8)
                   
        self.normal_frame.ok_btn = Button(self.normal_frame, text="OK", command=self.attack)

        block = [Label(self.normal_frame, text="\n      ",width=4 ) for i in range(0,15)]
        
        block[0].grid(row=0, column=0)
        block[1].grid(row=1, column=1)
        block[2].grid(row=1, column=3)
        block[3].grid(row=1, column=4)
        block[4].grid(row=4, column=7)
        block[5].grid(row=5, column=8)
        block[6].grid(row=6, column=9)
        block[7].grid(row=7, column=10)
        block[8].grid(row=7, column=11)
        

        self.normal_frame.h_label.grid(row=1, column=2)
        self.normal_frame.v_label.grid(row=2, column=2)
        self.normal_frame.i_label.grid(row=1, column=5, columnspan=2)
        self.normal_frame.w_scale.grid(row=2, column=5)
        self.normal_frame.r_cb.grid(row=2, column=6)
        self.normal_frame.n_label.grid(row=1, column=9)
        self.normal_frame.n_entry.grid(row=2, column=9)
        self.normal_frame.ok_btn.grid(row=8, column=12)
    
    def hostPage(self):
        self.clearWidget(2)
        self.level2bar = self.createMenuBar("hosts")
        self.clearViewBtn.pack_forget()

    def select(self, nodeName, index):
        if self.selected[index] is not None:
            # self.cframe.pack_forget()
            self.level3bar.buttons[index][int(self.selected[index].node.name[1:])].configure(style="UnSelected.TButton")
            self.level3bar.buttons[abs(index-1)][int(self.selected[index].node.name[1:])].state(["!disabled"])
            self.selected[index].pack_forget()

        self.selected[index] = self.consoles[nodeName]
        self.level3bar.buttons[index][int(nodeName[1:])].configure(style="Selected.TButton")
        self.level3bar.buttons[abs(index-1)][int(nodeName[1:])].state(["disabled"])
        self.cframe.pack( fill = "both", anchor=NW)
        if index == 0:
            self.selected[index].pack(expand = True, fill = 'both', side="left")
        elif index == 1:
            self.selected[index].pack(expand = True, fill = 'both', side="right")
        

    def hostFunc(self):
        self.clearWidget(3)
        self.level3bar = self.createMenuBar("hostFunc")
        self.clearViewBtn.pack_forget()

    def normal(self, event=None):
        self.clearWidget(4)
        self.normal_frame.pack(fill="both")
        self.cframe.pack(fill = "both", anchor=NW)
        self.normal_frame.v_label.configure(text=self.attack_frame.v_combo.get())

    def attack(self):
        self.clearWidget(4)
        self.attack_frame.pack(fill = "both")
        self.cframe.pack( fill = "both", anchor=NW)

    def changeAttackerNum(self, event, host_list):
        if self.attacker != []:
            for a, random, r, w, num_in, t in self.attacker:
                a.grid_forget()
                random.grid_forget()
                w.grid_forget()
                num_in.grid_forget()

                a.destroy()
                random.destroy()
                w.destroy()
                num_in.destroy()

        self.attacker = []
        for i in range(0, int(self.attack_frame.a_num_combo.get())):
            a = Combobox(self.attack_frame, values=host_list, width=6)
            a.current(i+1)
            r = IntVar()
            w = Scale(self.attack_frame, from_=0.04, to=1,orient=HORIZONTAL,resolution=0.01, background="white")
            w.set(0.3)
            random = Checkbutton(self.attack_frame, text="random", variable=r,onvalue=1, offvalue=0)

            t = IntVar()
            t.set(500)
            num_in = Entry(self.attack_frame, textvariable=t, width=8)
            
            a.grid(row=3+i, column=3)
            w.grid(row=3+i, column=5)
            random.grid(row=3+i, column=6)
            num_in.grid(row=3+i, column=8)

            self.attacker.append([a, random, r, w, num_in, t])
            
            
            

    def acceptAttack(self, victim):
        tmp = []
        if self.controller_th == None or self.controller_th.isAlive() == False:
            messagebox.showerror("Error", "The controller is closed !!")
            return

        for a, random, r, w, num_in, t in self.attacker:
            if victim.get() == a.get():
                messagebox.showerror("Error", "Can not attack itself !!")
                return
            if a.get() in tmp:
                messagebox.showerror("Error", "There are the same attacker")
                return
            try:
                t.get()
            except ValueError:
                messagebox.showerror("Error", "You enter the wrong type !!\nPlease enter a number with type \"int\"")
                return
            else:
                if 0 > t.get() or t.get() > 5000:
                    messagebox.showwarning("Warning", "Please enter a number which value is between 0 to 5000 (both includiing) !!")
                    return
            tmp.append(a.get())

        # print victim.get(), a_num_combo.get(), attacker.get()
        victimIP = self.net.hosts[int(victim.get()[1:])-1].IP()

        # clear all host consoles
        for host in self.net.hosts:
            self.consoles[host.name].handleInt()
            self.consoles[host.name].clear()


        self.consoles['h3'].sendCmd("python dns_server.py")

        n = -1 if self.normal_frame.r_var.get() == 1 else float(self.normal_frame.w_scale.get())
        self.consoles[victim.get()].sendCmd("python ge_dns.py "+str(self.normal_frame.t_var.get())+" "+str(n)+" | python victim.py")
        
        self.event.clearAttacker()
        for a, random, r, w, num_in, t  in self.attacker:
            n = -1 if r.get() == 1 else float(w.get())
            self.consoles[a.get()].sendCmd("python ge_dns.py "+str(t.get())+" "+str(n)+" | python attacker.py "+victimIP)
            self.event.putAttacker(
                    name = a.get(),
                    mac = self.net.hosts[int(a.get()[1:])-1].MAC())

            victimMac = self.net.hosts[int(self.attack_frame.v_combo.get()[1:])-1].MAC()
        self.event.setVictim(
                    name = self.attack_frame.v_combo.get(),
                    mac = victimMac)
        
        self.hostView()

    def stopAttack(self):
        for host in self.net.hosts:
            self.consoles[host.name].handleInt()
            self.consoles[host.name].sendCmd("echo \"========= End =========\"")

    def hostView(self):
        self.clearWidget(3)
        self.level3bar = self.createMenuBar("hostView")
        if self.selected[0] != None or self.selected[1] != None:
            self.cframe.pack( fill = "both", anchor=NW)
        self.clearViewBtn.pack(side="left")

        if self.selected[0] != None:
            self.selected[0].pack(expand = True, fill = 'both', side="left")
            btn_index = int(self.selected[0].node.name[1:])
            self.level3bar.buttons[0][btn_index].configure(style="Selected.TButton")
            self.level3bar.buttons[1][btn_index].state(["disabled"])
            self.displayBtn(0, btn_index)

        if self.selected[1] != None:
            self.selected[1].pack(expand = True, fill = 'both', side="right")
            btn_index = int(self.selected[1].node.name[1:])
            self.level3bar.buttons[1][btn_index].configure(style="Selected.TButton")
            self.level3bar.buttons[0][btn_index].state(["disabled"])
            self.displayBtn(1, btn_index)

    def clearView(self):
        for host in self.net.hosts:
            self.consoles[host.name].clear()

    def moveViewBtn(self, group, side):
        """ 
        group: int : 0 or 1
        side:  str : "left" or "right"
        """

        # display rightside button
        if side == "right":
            self.level3bar.buttons[group][0].state(["!disabled"])
            for i in range(self.hostViewBarLeft[group], self.hostViewBarRight[group]+1):
                self.level3bar.buttons[group][i].pack_forget()
            self.hostViewBarLeft[group] += 1
            self.hostViewBarRight[group] += 1
            self.level3bar.buttons[group][-1].pack_forget()
            for i in range(self.hostViewBarLeft[group], self.hostViewBarRight[group]+1):
                self.level3bar.buttons[group][i].pack(side="left")

            self.level3bar.buttons[group][-1].pack(side="left")

            if self.hostViewBarRight[group] == self.hostCount:
                self.level3bar.buttons[group][-1].state(["disabled"])
            else:
                self.level3bar.buttons[group][-1].state(["!disabled"])
            
        # display leftside button
        elif side == "left":
            self.level3bar.buttons[group][-1].state(["!disabled"])
            for i in range(self.hostViewBarLeft[group], self.hostViewBarRight[group]+1):
                self.level3bar.buttons[group][i].pack_forget()
            self.level3bar.buttons[group][-1].pack_forget()
            self.hostViewBarLeft[group] -= 1
            self.hostViewBarRight[group] -= 1
            for i in range(self.hostViewBarLeft[group], self.hostViewBarRight[group]+1):
                self.level3bar.buttons[group][i].pack(side="left")
            # self.level3bar.buttons[group][self.hostViewBarLeft[group]].pack(side="left", anchor="w")
            self.level3bar.buttons[group][-1].pack(side="left")

            if self.hostViewBarLeft[group] == 1:
                self.level3bar.buttons[group][0].state(["disabled"])
            else:
                self.level3bar.buttons[group][0].state(["!disabled"])
        
    def displayBtn(self, group, btn_index):
        """ Used in Host - View """
        left = self.hostViewBarLeft[group] - btn_index
        right = btn_index - self.hostViewBarRight[group]
        while left > 0:
            self.moveViewBtn(group, "left")
            left -= 1

        while right > 0:
            self.moveViewBtn(group, "right")
            right -= 1

    def switchPage(self):
        self.clearWidget(2)

    def callController(self):
        if self.controller_th == None or self.controller_th.isAlive() == False:
            self.controller_th = Thread(target=mycontroller.main, args=(self.event,))
            self.controller_th.setDaemon(True)
            self.controller_th.start()

    def createMenuBar(self, level=None):
        f = Frame(self.cv, style="Menubar.TFrame")
        buttons = []
        
        if level == "menu":
            buttons = [
                ( 'Hosts', self.hostPage),
                # ( 'Switches', self.switchPage),
                ( 'Controller', self.callController ),
                ( 'Quit', self.quit)
            ]
        elif level == "hosts":
            buttons = [
                ( 'Function', self.hostFunc),
                ( 'View', self.hostView),
                ( 'Clear', self.clearView)
            ]
        elif level == "hostFunc":
            buttons = [
                ( 'Normal', self.normal),
                ( 'Attack', self.attack),
                ( 'Stop', self.stopAttack)
            ]
        elif level == "hostView":
            f1 = Frame(f, width=self.width /2)
            f2 = Frame(f, width=self.width/2)
            btn_obj = [[],[]]
            l1 = Button(f1, text="<", command=partial(self.moveViewBtn, 0, "left"), width=1)
            r1 = Button(f1, text=">", command=partial(self.moveViewBtn, 0, "right"), width=1)
            l2 = Button(f2, text="<", command=partial(self.moveViewBtn, 1, "left"), width=1)
            r2 = Button(f2, text=">", command=partial(self.moveViewBtn, 1, "right"), width=1)

            l1.state(["disabled"])
            l2.state(["disabled"])
            l1.pack(side='left')
            l2.pack(side='left')


            btn_obj[0].append(l1)
            btn_obj[1].append(l2)
            
            self.hostViewBarLeft = [1,1]
            self.hostViewBarRight= [8,8]

            for i in range(0, self.hostCount):
                name = 'h'+str(i+1)
                cmd1 = partial(self.select, name, 0)
                cmd2 = partial(self.select, name, 1)
                b1 = Button(f1, text=name, command=cmd1, width=3, style="UnSelected.TButton")
                b2 = Button(f2, text=name, command=cmd2, width=3, style="UnSelected.TButton")

                self.viewBtnLen = 8
                if i < self.viewBtnLen:
                    b1.pack(side='left')
                    b2.pack(side='left')
                else:
                    b1.pack_forget()
                    b2.pack_forget()
                btn_obj[0].append(b1) 
                btn_obj[1].append(b2) 
    
            btn_obj[0].append(r1)
            btn_obj[1].append(r2)

            r1.pack(side='right')
            r2.pack(side='right')

            f1.pack(side="left")
            f2.pack(side="right")
            f.pack(padx = 4, pady = 4, expand=False, fill="none")
            return Object(frame=f, subframe=[f1,f2], buttons=btn_obj)
                
                
            

        btn_obj = []
        if level != None:
            for name, cmd in buttons:
                if level != "hostView":
                    b = Button(f, text=name, command=cmd)
                    b.pack(side='left')
                    btn_obj.append(b)
                    if name == "Clear":
                        self.clearViewBtn = b
        
        f.pack(padx = 4, pady = 4, fill = 'none', expand=False, anchor='nw')
        return Object(frame = f, buttons = btn_obj)

    def clearWidget(self, level):
        if level == 2:
            self.level2bar.frame.pack_forget()
            self.level2bar.frame.destroy()
        if level <= 3:
            self.level3bar.frame.pack_forget()
            self.level3bar.frame.destroy()
            # self.cframe.pack_forget()
        if level <= 4:
            self.attack_frame.pack_forget()
            self.normal_frame.pack_forget()
            for term in self.selected:
                if term is not None:
                    term.pack_forget()



if __name__ == '__main__':
    setLogLevel('info')
    network = TreeNet(depth=2, fanout=4)
    # network = None
    root = Tk()
    root.title( 'Mininet' ) 
    root.geometry('800x400')
    app = MainConsole(network, parent=root, width=800, height=400)
    app.mainloop()
