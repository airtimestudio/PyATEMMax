import PyATEMMax 
import argparse
import time
import random

print(PyATEMMax.test())

from typing import Dict, Any
ip       = "192.168.220.200"
switcher = PyATEMMax.ATEMMax()


def onConnect(params):
    print(f"Connected to switcher at {params['switcher'].ip}")
    switcher.setTransitionNextTransition(0,1)
    # switcher.setTransitionStyle(switcher.16 transitionSytle)

def onReceive(params: Dict[Any, Any]) -> None:
    """Called when data is received from the switcher"""
    if(params['cmd'] == 'RTMD'):
        print("rec disk info")
    if(params['cmd'] == 'RTMR'):
        print("rec timer")
        switcher.askForTime()
        print("asking for time")
        # print( self.switcher._udp.record_timer)

    print(f"[{time.ctime()}] Received [{params['cmd']}]: {params['cmdName']}")


# print(switcher.atem.nexTransitionStyles.bkgd)

switcher.registerEvent(switcher.atem.events.connect, onConnect)
# switcher.registerEvent(switcher.atem.events.receive, onReceive)




switcher.connect(ip)