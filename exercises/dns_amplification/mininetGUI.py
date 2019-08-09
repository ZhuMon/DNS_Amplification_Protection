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
        Frame.__init__( self, parent, height=height, width=width)
        
        self.net = net
        self.node = node
        self.prompt = node.name + '# '
        self.height, self.width, self.title = height, width, title

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
        self.width = 600
        self.top.geometry(str(self.width)+'x'+str(self.height))

        self.net = net
        self.menubar = self.createMenuBar("menu")
        self.level2bar = self.createMenuBar(None)
        self.level3bar = self.createMenuBar(None)


        cframe = self.cframe = Frame(self)
        self.consoles = {}
        titles = {
            'hosts': 'Host',
            'switches': 'Switch'
        }
        for name in titles:
            nodes = getattr(net, name)
            self.createConsoles( cframe, nodes, titles[name] )
        self.selected = [None, None]
        
        # self.cframe.pack(expand=True, fill='both')

        # graph = Graph(cframe)
        # self.consoles['graph'] = Object(frame = graph, consoles = [graph])
        # self.graph = graph
        # self.graphVisible = False
        self.updates = 0
        self.hostCount = len(self.net.hosts)
        self.bw = 0

        self.pack(expand=True, fill='both')

    def createConsoles(self, parent, nodes, title):
        "Create a grid of consoles in a frame."
        for node in nodes:
            self.consoles[node.name] = Console(parent, self.net, node, width=self.width/2, title = title)
        
    
    def hostPage(self):
        self.level2bar.frame.pack_forget()
        self.level2bar.frame.destroy()
        self.level3bar.frame.pack_forget()
        self.level3bar.frame.destroy()
        self.cframe.pack_forget()
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
        self.level3bar.frame.pack_forget()
        self.level3bar.frame.destroy()
        self.cframe.pack_forget()
        self.level3bar = self.createMenuBar("hostFunc")

    def attack(self):
        None

    def ping(self):
        None

    def iperf(self):
        None

    def hostView(self):
        self.level3bar.frame.pack_forget()
        self.level3bar.frame.destroy()
        self.level3bar = self.createMenuBar("hostView")

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
            for i in range(0, self.hostCount):
                name = 'h'+str(i+1)
                cmd1 = partial(self.select, name, 0)
                cmd2 = partial(self.select, name, 1)
                b1 = Button(f1, text=name, command=cmd1, width=4)
                b2 = Button(f2, text=name, command=cmd2, width=4)
                if i < 6:
                    b1.pack(side='left')
                    b2.pack(side='left')
                else:
                    b1.pack_forget()
                    b2.pack_forget()
                btn_obj[0].append(b1) 
                btn_obj[1].append(b2) 
    
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




if __name__ == '__main__':
    setLogLevel('info')
    network = TreeNet(depth=2, fanout=4)
    # network = None
    app = MainConsole(network)
    app.mainloop()
