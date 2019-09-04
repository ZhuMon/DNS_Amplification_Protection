import sys
import os
from time import sleep
import threading

from Tkinter import *
from ttk import *

from mininet.examples.consoles import *

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '../utils/'))

from run_exercise import *
from mininetGUI import *


if __name__ == '__main__':
    args = get_args()
    exercise = ExerciseRunner(args.topo, args.log_dir, args.pcap_dir,
                            args.switch_json, args.behavioral_exe, args.quiet)

    # exercise.run_exercise() 
    exercise.create_network()
    exercise.net.start()
    sleep(1)

    exercise.program_hosts()
    exercise.program_switches()

    sleep(1)
    
    # app = ConsoleApp(exercise.net, width=4 )
    root = Tk()
    root.title( 'Mininet' ) 
    root.geometry('800x400')
    app = MainConsole(exercise.net, parent=root)
    
    app.mainloop()
    # gui_th = threading.Thread(target=app.mainloop)
    # gui_th.setDaemon(True)
    # gui_th.start()


    # exercise.do_net_cli()
    # exercise.net.stop()
