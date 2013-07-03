"""
topy.py 
This file defines methods for operating network topology.

"""

import sys, os, json

class Topo(object):

    def __init__(self, *args, **kwargs):
        super(Topo, self).__init__(*args, **kwargs)
        self.topo = {}
        self.sw_outport = {}
        self.sw_type = {}
       
        # test data
        self.sw_outport[1] = {}
        self.sw_outport[1][1] = [2, 3]
        self.sw_outport[1][2] = []
        self.sw_outport[1][3] = []
        self.sw_type[1] = 0
        self.sw_type[2] = 1
        self.sw_type[3] = 1

    def LoadTopo(self, file_name):
        # Read file
        file = open(file_name, "r")
        json_str = ''
        # Get data
        while True:
            str = file.readline()
            if len(str) == 0:
                file.close()
                break
            json_str += str.replace('\n', '').strip()
        # Load JSON
        topo = json.loads(json_str)
        self.topo = topo
    
    def switch_outport(self, src_mac ,dpid):
        src_id = int(src_mac.replace(':',''), 16)
        return self.sw_outport[src_id][dpid]
        
    def switch_type(self, dpid):
        return self.sw_type[dpid]
        
        
