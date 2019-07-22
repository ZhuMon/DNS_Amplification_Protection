from Tkinter import *
from PIL import Image, ImageTk
import numpy as np

g_height = 500
g_width = 500


class ControllerGui():
    def __init__(self, links, nodes):
        root = Tk()
        self.cv = Canvas(root,bg = 'white', height = g_height, width = g_width)

        self.links = links
        self.nodes = nodes

        self.var = StringVar()
        self.L1 = Label(root, textvariable=self.var, width=30, height=2)
        self.L1.pack(side = LEFT )

        self.create_node()

        self.cv.pack()
        self.cv.bind('<Motion>' , self.move_handler)
        root.mainloop()

    def create_node(self):
        img_sw = Image.open("Img/switch.png").resize((40, 40), Image.ANTIALIAS)
        # img_ctr = Image.open("Img/controller.png").resize((40, 40), Image.ANTIALIAS)
        img_host = Image.open("Img/host.png").resize((40, 40), Image.ANTIALIAS)
        # img_pkt = Image.open("Img/packet.png").resize((40, 40), Image.ANTIALIAS)
        self.photo_sw = ImageTk.PhotoImage(img_sw)
        # self.photo_ctr = ImageTk.PhotoImage(img_ctr)
        self.photo_host = ImageTk.PhotoImage(img_host)
        # self.photo_pkt = ImageTk.PhotoImage(img_pkt)

        for node, pos in self.nodes.items():
            pos[0] = (pos[0]+2)*125
            pos[1] = (pos[1]+2)*125

        for link in self.links:
            self.cv.create_line(self.nodes[link[0]][0]+10, self.nodes[link[0]][1]+10, self.nodes[link[1]][0]+10, self.nodes[link[1]][1]+10)

        switches = []
        hosts = []
        for node, pos in self.nodes.items():
            if node[15:] == "00" :
                sw = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_sw)
                switches.append(sw)
            else:
                host = self.cv.create_image(pos[0]+10, pos[1]+10, image=self.photo_host)
                hosts.append(host)

    def move_handler(self, event):
        self.var.set('')
        
        for node, pos in self.nodes.items():
            if  pos[0] < event.x < pos[0]+20 and pos[1] < event.y < pos[1]+20:
                self.var.set(node)
                break

def main():
    nodes = {'00:00:00:00:03:03': np.array([ 0.01580925, -0.60809051]), '00:00:00:01:03:00': np.array([-0.54357307,  0.07891845]), '00:00:00:02:03:00': np.array([0.53874966, 0.10701586]), '00:00:00:03:03:00': np.array([ 0.00307517, -0.11810217]), '00:00:00:00:02:02': np.array([0.98593898, 0.29597483]), '00:00:00:00:01:01': np.array([-1.        ,  0.24428355])}
    links = [('00:00:00:00:03:03', '00:00:00:03:03:00'), ('00:00:00:01:03:00', '00:00:00:03:03:00'), ('00:00:00:01:03:00', '00:00:00:00:01:01'), ('00:00:00:02:03:00', '00:00:00:03:03:00'), ('00:00:00:02:03:00', '00:00:00:00:02:02')]

    #img_sw = Image.open("Img/switch.png").resize((50, 50), Image.ANTIALIAS)
    #img_ctr = Image.open("Img/controller.png").resize((50, 50), Image.ANTIALIAS)
    #img_host = Image.open("Img/host.png").resize((50, 50), Image.ANTIALIAS)
    #img_pkt = Image.open("Img/packet.png").resize((50, 50), Image.ANTIALIAS)
    #photo_sw = ImageTk.PhotoImage(img_sw)
    #photo_ctr = ImageTk.PhotoImage(img_ctr)
    #photo_host = ImageTk.PhotoImage(img_host)
    #photo_pkt = ImageTk.PhotoImage(img_pkt)

    c = ControllerGui(links, nodes)
if __name__ == '__main__':
    main()
