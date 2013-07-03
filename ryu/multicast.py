
import logging
import struct

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import nx_match
from ryu.lib.mac import haddr_to_str
from ryu.lib.mac import haddr_to_bin
#from ryu.lib.ip import ipv4_to_bin
import topo

class Multicast(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    #Topo = lambda: topo.Topo()
    
    def __init__(self, *args, **kwargs):
        super(Multicast, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.Topo = topo.Topo()
        self.Topo.LoadTopo("/home/ubuntu/mininet/custom/topo.json")

    def ipv4_to_int(self, string):
        ip = string.split('.')
        assert len(ip) == 4
        i = 0
        for b in ip:
            b = int(b)
            i = (i << 8) | b
        return i

    def add_action(self, dp, action):
        rule = nx_match.ClsRule()
        self.send_flow_mod(
                dp, rule, 0, dp.ofproto.OFPFC_ADD, 0, 0, None,
                0xffffffff, None, dp.ofproto.OFPFF_SEND_FLOW_REM, action)

    def send_flow_mod(self, dp, rule, cookie, command, idle_timeout,
                      hard_timeout, priority=None, buffer_id=0xffffffff,
                      out_port=None, flags=0, actions=None):
        if priority is None:
            priority = dp.ofproto.OFP_DEFAULT_PRIORITY
        if out_port is None:
            out_port = dp.ofproto.OFPP_NONE

        match_tuple = rule.match_tuple()
        match = dp.ofproto_parser.OFPMatch(*match_tuple)

        m = dp.ofproto_parser.OFPFlowMod(
                dp, match, cookie, command, idle_timeout, hard_timeout,
                priority, buffer_id, out_port, flags, actions)
        dp.send_msg(m)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        dst, src, _eth_type = struct.unpack_from('!6s6sH', buffer(msg.data), 0)

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s",
                         dpid, haddr_to_str(src), haddr_to_str(dst),
                         msg.in_port)

        if self.Topo.switch_type(dpid) == 0:
            # Swtich - on the way 
            self.logger.info("! sw on the way")
            # Query for dest port
            outport_list = self.Topo.switch_outport(dpid) 
            for port in outport_list:
                action = datapath.ofproto_parser.OFPActionOutput(port)
                self.add_action(datapath, [action, ])
                #actions = [datapath.ofproto_parser.OFPActionOutput(port)]
                #self.add_apply_actions(datapath, actions, msg)
                self.logger.info("! send to port %s", str(port))
        else:
            # Swtich - last hop
            self.logger.info("! sw last hop")
            # Dest: all port
            port = ofproto.OFPP_ALL
            act_port = datapath.ofproto_parser.OFPActionOutput(port, 0)
            ## Set dest IP
            ##nw_dst = '10.0.0.2'
            ##nw_dst_int = self.ipv4_to_int(nw_dst)
            ##act1 = datapath.ofproto_parser.OFPActionSetNwDst(nw_dst_int)
            # Set MAC
            dl_dst = 'ff:ff:ff:ff:ff:ff'
            dl_dst_bin = haddr_to_bin(dl_dst)
            act_mac = datapath.ofproto_parser.OFPActionSetDlDst(dl_dst_bin)
            self.add_action(datapath, [act_port, act_mac])
            
