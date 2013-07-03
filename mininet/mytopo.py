"""
Run: sudo mn --custom mytopo.py --topo mytopo --switch ovsk --controller remote --mac --link tc
Topo: 
                 -- h2
          |-- s2 |
c1 -- s1 -|      -- h3
          |-- s3 -- h4
"""

import sys, os, json
from mininet.topo import Topo

def LoadTopo(file_name):
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
   return topo

class MyTopo( Topo ):
    
    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Load topology from file
        topo_data = LoadTopo("/home/ubuntu/mininet/custom/topo.json")
        # Add hosts and switches
        node = {}
        for name in topo_data["node"]:
            if name[0] == 's':
                # Switch
                node[name] = self.addSwitch( str(name) )
            elif name[0] in {'c', 'h'}:
                # Camara or Host
                node[name] = self.addHost( str(name) )
        
        # Add links
        for link_obj in topo_data["link"]:
           # Data mapping
           src = node[ link_obj["src"] ]
           dst = node[ link_obj["dst"] ]
           p1 = link_obj["p1"]
           p2 = link_obj["p2"]
           linkopts = dict(bw=link_obj["bw"], delay=link_obj["delay"])
           # Set link
           self.addLink( src, dst, port1=p1, port2=p2, **linkopts )

topos = { 'mytopo': ( lambda: MyTopo() ) }

