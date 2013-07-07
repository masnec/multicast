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
        # set default descriptor = 1
        self.K = 1

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
        if file_name:
            # Load flow from json file
            self.load_flow(file_name)
        if not hasattr(self, "map_sw_port"):
            self.create_switch_info()
        
        # Update sw_outport
        ## for each camera
        for camera in self.flow:
            cam_id = int(camera[1:])
            self.sw_outport[cam_id] = {}
            ## for each descriptor k
            for k in self.flow[camera]:
                k_id = int(k[1:])
                self.sw_outport[cam_id][k_id] = {}
                ## for each source link
                for src_sw in self.flow[camera][k]:
                    src_id = int(src_sw[1:])
                    # Reset outport
                    self.sw_outport[cam_id][k_id][src_id] = []
                    for dst_sw in self.flow[camera][k][src_sw]:
                        dst_id = int(dst_sw[1:])
                        (src_port, dst_port) = self.map_sw_port[(src_id, dst_id)]
                        # Append port
                        self.sw_outport[cam_id][k_id][src_id].append(src_port)

    def switch_outport(self, camera_mac ,dpid, k_id):
        # Convert MAC to host ID
        camera_id = int(camera_mac.replace(':',''), 16)
        try:
            return self.sw_outport[camera_id][k_id][dpid]
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

    def convert_k_id_to_ip(self, id):
        # Start from 224.0.0.0
        ip = (224<<24) + id
        return ".".join(map(lambda n: str(ip>>n & 0xFF), [24,16,8,0]))
        
    def cplex_generate_input(self, file_name):
        # Get node types
        num_source = 0
        num_host = 0
        num_switch = 0
        for obj in self.topo["node"]:
            if obj[0] == 'c':
                num_source +=1
            elif obj[0] == 'h':
                num_host +=1
            else:
                num_switch +=1
        total_node = num_source + num_host + num_switch

        # Matrix ID mapping
        id_map = {}
        ## source, host, switch
        for id in range(1, num_source + 1):
            id_map['c'+str(id)] = id
        for id in range(1, num_host + 1):
            id_map['h'+str(id + num_source)] = id + num_source
        for id in range(1, num_switch + 1):
            id_map['s'+str(id)] = id + num_source + num_host
        
        # Build link matrix
        link = {}
        ## init
        for i in range(1, total_node + 1):
            link[i] = {}
            for j in range(1, total_node + 1):
                link[i][j] = 0
        ## get data
        for obj in self.topo["link"]:
            link[ id_map[ obj["src"] ] ][ id_map[ obj["dst"] ] ] = 1

        # Generate string
        output = ""
        
        output += "K = " + str(self.K)  + "\n"
        output += "S = " + str(num_source) + "\n"
        output += "H = " + str(num_host) + "\n"
        
        output += "SW = " + str(num_switch) + "\n"
        output += "S_LIST = [ " + " ".join(map(lambda n:str(n), range(1, num_source + 1))) + " ]\n"
        output += "H_LIST = [ " + " ".join(map(lambda n:str(n), range(num_source + 1, num_host + num_source + 1))) + " ]\n"
        output += "SW_LIST = [ " \
                +  " ".join(map(lambda n:str(n), range(num_source + num_host + 1, total_node + 1))) + " ]\n"
        
        ## add link map
        output += "LINK = [ \n"
        for i in range(1, total_node +1):
            output += "[ "
            for j in range(1, total_node + 1):
                output += str(link[i][j]) + " "
            output += "]\n"
        output += "] \n"
        
        with open(file_name, "w") as file:
            file.write(output)
    
    def cplex_read_output(self, file_name):
        # Get node types
        num_source = 0
        num_host = 0
        num_switch = 0
        for obj in self.topo["node"]:
            if obj[0] == 'c':
                num_source +=1
            elif obj[0] == 'h':
                num_host +=1
            else:
                num_switch +=1
        total_node = num_source + num_host + num_switch
        
        # Matrix ID mapping
        id_map = {}
        ## source, host, switch
        for id in range(1, num_source + 1):
            id_map[id] = 'c'+str(id)
        for id in range(1, num_host + 1):
            id_map[id + num_source] = 'h'+str(id + num_source)
        for id in range(1, num_switch + 1):
            id_map[id + num_source + num_host] = 's'+str(id)
        
        with open(file_name, "r") as file:
            # Reset flow
            self.flow = {}
            
            # For each camera
            for camera_id in range(1, num_source + 1):
                camera = 'c'+str(camera_id)
                self.flow[camera] = {}
                
                # For each descriptor 
                for k_id in range(1, self.K + 1):
                    k = 'k'+str(k_id)
                    self.flow[camera][k] = {}
                    
                    # For each link source
                    for src_id in range(1, total_node + 1):
                        # Process data from file
                        line = file.readline()
                        while line.strip() == "":
                            line = file.readline()
                        conns = line.strip().split(" ")
                        
                        # only record link from switches
                        if src_id <= total_node - num_switch:
                            continue
                        src_node = id_map[src_id]
                        self.flow[camera][k][src_node] = []
                        
                        # For each link dest
                        for dst_id in range(1, total_node + 1):
                            if conns[dst_id-1] == "1":
                                # Add to flow list
                                dst_node = id_map[dst_id]
                                self.flow[camera][k][src_node].append(dst_node)

