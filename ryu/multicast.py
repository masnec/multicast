
import logging
import struct
from threading import Timer
from ryu.base import app_manager
from ryu.controller import dpset
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
    
    _CONTEXTS = {'dpset': dpset.DPSet,}
    

    def __init__(self, *args, **kwargs):
        super(Multicast, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']

        self.mac_to_port = {}
        self.switches = {}
        self.Topo = topo.Topo()
        self.Topo.load_topo("../mininet/topo.json")
        #self.Topo.update_flow("flow.json")
        self.looper_update_flow()

    def looper_update_flow(self):
        self.logger.info("!!! Update flow")
        
        # Update flow info
        self.Topo.update_flow("flow.json")
        
        # Write to switches
        for dpid, datapath in self.switches.items():
            # Del all flows
            datapath.send_delete_all_flows()
            datapath.send_barrier()
            
            # For each camera
            for src_id in self.Topo.sw_outport:
                src_mac = self.Topo.convert_host_id_to_mac(src_id)
                self.logger.info("!!! -  Camera MAC: %s, dpid: %s",src_mac, str(dpid))
                outport_list = self.Topo.switch_outport(src_mac, dpid)
                
                # Match camera MAC
                rule = nx_match.ClsRule()
                rule.set_dl_src( haddr_to_bin(src_mac) )
                
                # Duplicate packet
                action_list = []
                for port in outport_list:
                    action = datapath.ofproto_parser.OFPActionOutput(port)
                    action_list.append(action)
                    self.logger.info("!!! --- Add port: %s", port)

                # Deal with different type of switch
                if len(action_list) > 0:
                    # At least one output
                    if self.Topo.switch_type(dpid) == 0:
                        # Switch - on the way
                        pass 
                    else:
                        # Switch - the last hop
                        # Set broadcast MAC
                        dl_dst = 'ff:ff:ff:ff:ff:ff'
                        dl_dst_bin = haddr_to_bin(dl_dst)
                        action = datapath.ofproto_parser.OFPActionSetDlDst(dl_dst_bin)
                        action_list.append(action)
                    # Send action
                    self.add_action(datapath, action_list, rule = rule)

        # Trigger next update
        Timer(10, self.looper_update_flow).start()
    
    def ipv4_to_int(self, string):
        ip = string.split('.')
        assert len(ip) == 4
        i = 0
        for b in ip:
            b = int(b)
            i = (i << 8) | b
        return i

    def add_action(self, dp, action, rule = None):
        if rule is None:
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
        #self.mac_to_port.setdefault(dpid, {})

        self.logger.info("!!! packet in dpid: %s, src_mac: %s, dst_mac: %s, in_port: %s",
                         dpid, haddr_to_str(src), haddr_to_str(dst),
                         msg.in_port)
    
    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def handler_datapath(self, ev):
        if ev.enter:
            self.logger.info('!!! datapath join, id = ' + str(ev.dp.id))
            # Add to switches
            self.switches[ev.dp.id] = ev.dp
        else:
            self.logger.info('!!! datapath leave, id = ' + str(ev.dp.id))
            # Del from switches
            self.switches.pop(ev.dp.id, None)
