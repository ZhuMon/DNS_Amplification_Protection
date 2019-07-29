from threading import _Event

class myEvent(_Event):
    def __init__(self, topology):
        super(myEvent, self).__init__()
        self.topology = topology
        self.objID = {} # store the tkinter ID of edges {1:13241232, ...}
        # DNS response
        self.r_pkt_num = {} # store 10s # of pkts on every edges {1: 24}
        self.r_all_pkt_num = {} # store all # of pkts on every edges {1: 134}
        # DNS query
        self.q_pkt_num = {} # store 10s # of pkts on every edges {1: 24}
        self.q_all_pkt_num = {} # store all # of pkts on every edges {1: 134}
        # self.port = {} # how many port does every switch have {1:2, 2:3}
        self.r_edge_update_flag = {} # record the edge whether updated {1:True,2:False}
        self.q_edge_update_flag = {} # record the edge whether updated {1:True,2:False}

        # init
        self.cleanFlag()


    def cleanFlag(self):
        for no, link in self.topology.items():
            self.r_edge_update_flag[no] = False
            self.q_edge_update_flag[no] = False

    def isUpdated(self, mac1, mac2, q_or_r = 'q', no=None):
        if no == None:
            no = self.findEdge(mac1, mac2)
        if q_or_r == 'q':
            return self.q_edge_update_flag[no]
        elif q_or_r == 'r':
            return self.r_edge_update_flag[no]

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

        if self.objID.has_key(edgeID) == False:
            self.objID[edgeID] = []
        self.objID[edgeID].append(objID)

    def getObjID(self, mac1, mac2, edgeID=None):
        if edgeID == None:
            edgeID = self.findEdge(mac1, mac2)
        
        return self.objID[edgeID]

    def getPktNum(self, mac1, mac2, q_or_r = 'q'):
        edgeID = self.findEdge(mac1, mac2)
        if q_or_r == 'q':
            if self.q_pkt_num.has_key(edgeID) is False:
                self.q_pkt_num[edgeID] = 0
            return self.q_pkt_num[edgeID]
        elif q_or_r == 'r':
            if self.r_pkt_num.has_key(edgeID) is False:
                self.r_pkt_num[edgeID] = 0
            return self.r_pkt_num[edgeID]

    def putPktNum(self, num, mac1, mac2, q_or_r = 'q'):
        edgeID = self.findEdge(mac1, mac2)
        if q_or_r == 'q':
            if self.q_all_pkt_num.has_key(edgeID):
                self.q_pkt_num[edgeID] = num - self.q_all_pkt_num[edgeID]
            else:
                self.q_pkt_num[edgeID] = num

            self.q_all_pkt_num[edgeID] = num
            self.q_edge_update_flag[edgeID] = True
        elif q_or_r == 'r':
            if self.r_all_pkt_num.has_key(edgeID):
                self.r_pkt_num[edgeID] = num - self.r_all_pkt_num[edgeID]
            else:
                self.r_pkt_num[edgeID] = num
            self.r_all_pkt_num[edgeID] = num
            self.r_edge_update_flag[edgeID] = True

