from Tkinter import *
from ttk import *
from functools import partial

from mininet.log import setLogLevel
from mininet.topolib import TreeNet
from mininet.examples.consoles import Graph, Console

# Make it easier to construct and assign objects

def assign( obj, **kwargs ):
    "Set a bunch of fields in an object."
    obj.__dict__.update( kwargs )

class Object( object ):
    "Generic object you can stuff junk into."
    def __init__( self, **kwargs ):
        assign( self, **kwargs )


class MainConsole( Frame ):
    " Console for Mininet. "

    menuStyle = { 'font': 'Geneva 12 bold'}

    def __init__( self, net, parent = None):
        Frame.__init__(self, parent)
        self.top = self.winfo_toplevel()
        self.top.title( 'Mininet' )
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
        self.selected = None
        
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
            self.consoles[node.name] = Console(parent, self.net, node, title = title)
        
    
    def hostPage(self):
        self.level2bar.pack_forget()
        self.level2bar.destroy()
        self.level3bar.pack_forget()
        self.level3bar.destroy()
        self.level2bar = self.createMenuBar("hosts")

    def select( self, groupName, nodeName):
        if self.selected is not None:
            self.cframe.pack_forget()
            self.selected.pack_forget()

        self.selected = self.consoles[nodeName]
        self.cframe.pack(expand = True, fill = "both")
        self.selected.pack(expand = True, fill = 'both')
        

    def hostFunc(self):
        self.level3bar.pack_forget()
        self.level3bar.destroy()
        self.cframe.pack_forget()
        self.level3bar = self.createMenuBar("hostFunc")

    def attack(self):
        None

    def ping(self):
        None

    def iperf(self):
        None

    def hostView(self):
        self.level3bar.pack_forget()
        self.level3bar.destroy()
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
            for i in range(0, self.hostCount):
                name = 'h'+str(i+1)
                buttons.append([name, partial(self.select,"hosts", name)])
                
        
        if level != None:
            for name, cmd in buttons:
                b = Button(f, text=name, command=cmd)
                b.pack(side='left')
        
        f.pack(padx = 4, pady = 4, fill = 'x')
        return f




if __name__ == '__main__':
    setLogLevel('info')
    network = TreeNet(depth=2, fanout=4)
    # network = None
    app = MainConsole(network)
    app.mainloop()
