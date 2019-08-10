from Tkinter import *
from ttk import *
from functools import partial

from mininet.log import setLogLevel
from mininet.topolib import TreeNet
from mininet.examples.consoles import Graph

# Make it easier to construct and assign objects

def assign( obj, **kwargs ):
    "Set a bunch of fields in an object."
    obj.__dict__.update( kwargs )

class Object( object ):
    "Generic object you can stuff junk into."
    def __init__( self, **kwargs ):
        assign( self, **kwargs )

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
            'font' : 'Monaco 12',
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
        self.tk.createfilehandler(self.node.stdout, READABLE,
                                  self.handleReadable)

    def append(self, text):
        self.text.insert('end', text)
        self.text.mark_set('insert', 'end')
        self.text.see('insert')
        outputHook = lambda x, y: True
        if self.outputHook:
            outputHook = self.ouptuHook
        outputHook(self, text)
        
    def sendCmd(self, cmd):
        if not self.node.waiting:
            self.node.sendCmd(cmd)

    def handleReadable(self, _fds, timeoutms=None):
        "Handle file readable event."
        data = self.node.monitor(timeoutms)
        self.append(data)
        if not self.node.waiting:
            self.append(self.prompt)

    def waiting(self):
        return self.node.waiting

    def waitOutput(self):
        while self.node.waiting:
            self.handleReadable(self,timeoutms=1000)
            self.update()
    
    def clear(self):
        self.text.delete('1.0','end')
    

class MainConsole( Frame ):
    " Console for Mininet. "

    menuStyle = { 'font': 'Geneva 12 bold'}

    def __init__( self, net, parent = None):
        Frame.__init__(self, parent)
        self.top = self.winfo_toplevel()
        self.top.title( 'Mininet' )
        self.height = 400
        self.width = 800
        self.top.geometry(str(self.width)+'x'+str(self.height))

        self.net = net
        self.menubar = self.createMenuBar("menu")
        self.level2bar = self.createMenuBar(None)
        self.level3bar = self.createMenuBar(None)

        self.initStyle()
        self.createCframe()
        
        # self.cframe.pack(expand=True, fill='both')

        # graph = Graph(cframe)
        # self.consoles['graph'] = Object(frame = graph, consoles = [graph])
        # self.graph = graph
        # self.graphVisible = False
        self.updates = 0
        self.hostCount = len(self.net.hosts)
        self.bw = 0

        self.pack(expand=True, fill='both')

    def initStyle(self):
        self.style = Style()
        self.style.configure("Attack.TFrame",
                background="white"
                )
        self.style.configure("TLabel",
                background="white"
                )

    def createConsoles(self, parent, nodes, title):
        "Create a grid of consoles in a frame."
        for node in nodes:
            self.consoles[node.name] = Console(parent, self.net, node, width=self.width/2, title = title)
        

    def createCframe(self):
        "Create a child frame."
        self.cframe = Frame(self)
        
        """ Hosts - View - consoles """
        self.consoles = {}
        titles = {
            'hosts': 'Host',
            'switches': 'Switch'
        }
        for name in titles:
            nodes = getattr(self.net, name)
            self.createConsoles( self.cframe, nodes, titles[name] )
        self.selected = [None, None]

        ###################################################
        """ Hosts - Function - Attack """
        self.attack_frame = Frame(self.cframe, style="Attack.TFrame")
        host_list = [h.name for h in self.net.hosts]
        host_list.remove('h3')
        choose_victim = Label(self.attack_frame, text="Choose a victim: ", width=15)
        v = Combobox(self.attack_frame, values=host_list, width=6)
        
        choose_attacker = Label(self.attack_frame, text="Choose attacker:", width=15)
        attacker_num = Label(self.attack_frame, text="attacker number:", width=15)
        num = Combobox(self.attack_frame, values=range(1, 6), width=5)
        
        attacker = Label(self.attack_frame, text="attacker", width=10)
        a = Combobox(self.attack_frame, values=host_list, width=6)
        
        accept = Button(self.attack_frame, text="Accept", command=None, width=10)
        
        block = [Label(self.attack_frame, text="",width=4 ) for i in range(0,15)]

        block[0].grid(row=0, column=0)
        block[1].grid(row=3, column=3)
        block[2].grid(row=4, column=4)
        block[3].grid(row=5, column=5)
        block[4].grid(row=6, column=6)
        block[5].grid(row=7, column=7)
        block[6].grid(row=8, column=8)
        block[7].grid(row=9, column=9)
        block[8].grid(row=10, column=10)
        block[9].grid(row=11, column=11)
        block[10].grid(row=12, column=12)

        choose_victim.grid(row=1, column=1)
        v.grid(row=1, column=2)
        choose_attacker.grid(row=2, column=1)
        attacker_num.grid(row=2, column=2)
        num.grid(row=2, column=3)
        attacker.grid(row=2, column=4)
        a.grid(row=2, column=5)
        accept.grid(row=14, column=14)

        
    
    def hostPage(self):
        self.clearWidget(2)
        self.level2bar = self.createMenuBar("hosts")

    def select(self, nodeName, index):
        if self.selected[index] is not None:
            # self.cframe.pack_forget()
            self.selected[index].pack_forget()

        self.selected[index] = self.consoles[nodeName]
        self.cframe.pack(expand = True, fill = "both")
        if index == 0:
            self.selected[index].pack(expand = True, fill = 'both', side="left")
        elif index == 1:
            self.selected[index].pack(expand = True, fill = 'both', side="right")
        

    def hostFunc(self):
        self.clearWidget(3)
        self.level3bar = self.createMenuBar("hostFunc")

    def attack(self):
        self.clearWidget(4)
        self.attack_frame.pack(expand = True, fill = "both")
        self.cframe.pack(expand = True, fill = "both")

    def ping(self):
        self.clearWidget(4)
        None

    def iperf(self):
        self.clearWidget(4)
        None

    def hostView(self):
        self.clearWidget(3)
        self.level3bar = self.createMenuBar("hostView")

    def moveViewBtn(self, group, side):
        """ 
        group: int : 0 or 1
        side:  str : "left" or "right"
        """

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
        

    def callController(self):
        None

    def createMenuBar(self, level=None):
        f = Frame(self)
        buttons = []
        
        if level == "menu":
            buttons = [
                ( 'Hosts', self.hostPage),
                ( 'Switches', None ),
                ( 'Controllers', self.callController ),
                ( 'Quit', self.quit)
            ]
        elif level == "hosts":
            buttons = [
                ( 'Function', self.hostFunc),
                ( 'View', self.hostView)
            ]
        elif level == "hostFunc":
            buttons = [
                ( 'Attack', self.attack),
                ( 'Ping', self.ping),
                ( 'Iperf', self.iperf)
            ]
        elif level == "hostView":
            f1 = Frame(f, width=self.width/2)
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
                b1 = Button(f1, text=name, command=cmd1, width=4)
                b2 = Button(f2, text=name, command=cmd2, width=4)
                if i < 8:
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
            f.pack(padx = 4, pady = 4, fill = 'x')
            return Object(frame=f, subframe=[f1,f2], buttons=btn_obj)
                
                
            

        btn_obj = []
        if level != None:
            for name, cmd in buttons:
                if level != "hostView":
                    b = Button(f, text=name, command=cmd)
                    b.pack(side='left')
                    btn_obj.append(b)
        
        f.pack(padx = 4, pady = 4, fill = 'x')
        return Object(frame = f, buttons = btn_obj)

    def clearWidget(self, level):
        if level == 2:
            self.level2bar.frame.pack_forget()
            self.level2bar.frame.destroy()
        if level <= 3:
            self.level3bar.frame.pack_forget()
            self.level3bar.frame.destroy()
            self.cframe.pack_forget()
        if level <= 4:
            self.attack_frame.pack_forget()
            for term in self.selected:
                if term is not None:
                    term.pack_forget()



if __name__ == '__main__':
    setLogLevel('info')
    network = TreeNet(depth=2, fanout=4)
    # network = None
    app = MainConsole(network)
    app.mainloop()
