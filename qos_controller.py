from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp


class QoSController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(QoSController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def add_flow(self, datapath, priority, match, actions):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Table miss rule
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 0, match, actions)

        self.logger.info("Switch connected")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        arp_pkt = pkt.get_protocol(arp.arp)

        dpid = datapath.id
        in_port = msg.match['in_port']

        # Initialize MAC table
        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}

        # Learn MAC
        self.mac_to_port[dpid][eth.src] = in_port

        # Handle ARP (must flood)
        if arp_pkt:
            out_port = ofproto.OFPP_FLOOD
        else:
            # Learning switch forwarding
            if eth.dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][eth.dst]
            else:
                out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # QoS FLOW INSTALLATION (CORRECT MATCH)
        if ip_pkt:
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            if src_ip == "10.0.0.1":
                priority = 100
                label = "HIGH PRIORITY"
            else:
                priority = 10
                label = "LOW PRIORITY"

            match = parser.OFPMatch(
                in_port=in_port,
                eth_type=0x0800,
                ipv4_src=src_ip,
                ipv4_dst=dst_ip,
                eth_dst=eth.dst
            )

            # Clean logs for demo
            self.logger.info("===================================")
            self.logger.info("QoS Applied")
            self.logger.info("Source      : %s", src_ip)
            self.logger.info("Destination : %s", dst_ip)
            self.logger.info("Type        : %s", label)
            self.logger.info("Priority    : %d", priority)
            self.logger.info("Out Port    : %s", out_port)
            self.logger.info("===================================")

            self.add_flow(datapath, priority, match, actions)

        # Send packet
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )
        datapath.send_msg(out)
