import sys
import os
from time import sleep

from Tkinter import *
# from ttk import *

from mininet.examples.consoles import *

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '../../utils/'))

from run_exercise import *


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
    app = ConsoleApp(exercise.net, width=4 )
    app.mainloop()
    exercise.do_net_cli()
    exercise.net.stop()
