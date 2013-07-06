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
        """
        self.sw_outport[1] = {}
        self.sw_outport[1][1] = [2, 3]
        self.sw_outport[1][2] = []
        self.sw_outport[1][3] = []
        self.sw_type[1] = 0
        self.sw_type[2] = 1
        self.sw_type[3] = 1
        """
        #self.load_topo('../mininet/topo.json')
        #self.update_flow('flow.json')
        #print self.topo
        #print self.sw_outport
        #print self.sw_type

    def load_json(self, file_name):
        # Read file
        json_str = ''
        with open(file_name, "r") as file:
            for line in file:
                json_str += line.replace('\n', '').strip()
        # Load JSON
        data = json.loads(json_str)
        return data
    
    def load_topo(self, file_name):
        self.topo = self.load_json(file_name)

    def load_flow(self, file_name):
        self.flow = self.load_json(file_name)

    def create_switch_info(self):
        # Build relation between switch and port
        ## (sw_src, sw/host_dst) -> (port_src, port_dst)
        self.map_sw_port = {}

        # Build switch type
        self.sw_type = {}
        
        for link in self.topo["link"]:
            # For each switch link
            if link["src"][0] == 's':
                src_id = int(link["src"][1:])
                dst_id = int(link["dst"][1:])
                # Create relation
                self.map_sw_port[(src_id, dst_id)] = (link["p1"], link["p2"])
                # Create switch type
                if link["dst"][0] == 's':
                    # Intermediate switch
                    if not src_id in self.sw_type:
                        self.sw_type[src_id] = 0
                else:
                    # Last hop switch
                    if not src_id in self.sw_type:
                        self.sw_type[src_id] = 1
    
    def update_flow(self, file_name = None):
        # Load flow from json file
        self.load_flow(file_name)
        if not hasattr(self, "map_sw_port"):
            self.create_switch_info()
        
        # Update sw_outport
        for camera in self.flow:
            cam_id = int(camera[1:])
            self.sw_outport[cam_id] = {}
            for src_sw in self.flow[camera]:
                src_id = int(src_sw[1:])
                # Reset outport
                self.sw_outport[cam_id][src_id] = []
                for dst_sw in self.flow[camera][src_sw]:
                    dst_id = int(dst_sw[1:])
                    (src_port, dst_port) = self.map_sw_port[(src_id, dst_id)]
                    # Append port
                    self.sw_outport[cam_id][src_id].append(src_port)

    def switch_outport(self, src_mac ,dpid):
        # Convert MAC to host ID
        src_id = int(src_mac.replace(':',''), 16)
        try:
            return self.sw_outport[src_id][dpid]
        except:
            return []

    def switch_type(self, dpid):
        # Type 0 -> intermediate, 1 -> last hop
        return self.sw_type[dpid]
        
    def convert_host_id_to_mac(self, id):
        # Can do this because mininet uses the same id for mac and ip
        # Start from 00:00:00:00:00:00
        return ":".join(map(lambda n: "%02x" % (id>>n & 0xFF), [40,32,24,16,8,0]))

    def convert_host_id_to_ip(self, id):
        # Can do this because mininet uses the same id for mac and ip
        # Start from 10.0.0.0
        ip = (10<<24) + id
        return ".".join(map(lambda n: str(ip>>n & 0xFF), [24,16,8,0]))

