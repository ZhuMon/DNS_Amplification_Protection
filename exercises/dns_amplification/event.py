from threading import _Event

class myEvent(_Event):
    def __init__(self, topology):
        super(myEvent, self).__init__()
        self.topology = topology
        self.objID = {} # store the tkinter ID of edges {1:13241232, ...}
        self.pkt_num = {} # store 10s # of pkts on every edges {1: 24}
        self.all_pkt_num = {} # store all # of pkts on every edges {1: 134}
        # self.port = {} # how many port does every switch have {1:2, 2:3}
        self.edge_update_flag = {} # record the edge whether updated {1:True,2:False}
        # init
        self.cleanFlag()


    def cleanFlag(self):
        for no, link in self.topology.items():
            self.edge_update_flag[no] = False

    def isUpdated(self, mac1, mac2, no=None):
        if no == None:
            no = self.findEdge(mac1, mac2)
        return self.edge_update_flag[no]

    def findEdge(self, mac1, mac2):
        """ return the index in topology """
        for no, link in self.topology.items():
            m1 = link.keys()[0]
            m2 = link.keys()[1]
            if m1 == mac1 and m2 == mac2:
                return no
            elif m1 == mac2 and m2 == mac1:
                return no

    def putObjID(self, objID, mac1=None, mac2=None, edgeID=None):
        if edgeID == None and mac1 != None and mac2 != None:
            edgeID = self.findEdge(mac1, mac2)
        elif mac1 == None or mac2 == None:
            print "putObjID error"

        self.objID[edgeID] = objID

    def getObjID(self, mac1, mac2, edgeID=None):
        if edgeID == None:
            edgeID = self.findEdge(mac1, mac2)
        
        return self.objID[edgeID]

    def getPktNum(self, mac1, mac2):
        edgeID = self.findEdge(mac1, mac2)
        return self.pkt_num[edgeID]

    def putPktNum(self, num, mac1, mac2):
        edgeID = self.findEdge(mac1, mac2)
        if self.all_pkt_num.has_key(edgeID):
            self.pkt_num[edgeID] = num - self.all_pkt_num[edgeID]
        else:
            self.pkt_num[edgeID] = num

        self.all_pkt_num[edgeID] = num
        self.edge_update_flag[edgeID] = True
