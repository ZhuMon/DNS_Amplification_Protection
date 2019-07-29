/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>
//#include <psa.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_IPV6 = 0x86dd;
const bit<16> TYPE_LLDP = 0x88cc;
const bit<16> TYPE_PIN = 0x88ce;
const bit<16> TYPE_POUT = 0x88cf;
const bit<8>  TYPE_UDP  = 0x11;
const bit<32> NUM = 65536;
const bit<32> MAX_NUM = 8;
const bit<9> CPU_PORT = 255;
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
//typedef bit<64> ip6Addr_t;
typedef bit<16> mcast_group_t;
typedef bit<2> MeterColor;
const MeterColor MeterColor_GREEN = 2w1;
const MeterColor MeterColor_YELLOW = 2w2;

header ethernet_t {
    macAddr_t dstAddr; 
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

/*header ipv6_t {
    bit<4>    version;
    bit<8>    trafficClass;
    bit<20>   flowLabel;
    bit<16>   payloadLen;
    bit<8>    nextHeader;
    bit<8>    hlim;
    ip6Addr_t srcAddr;
    ip6Addr_t dstAddr;
}*/

header udp_t {
    bit<16>   sport;
    bit<16>   dport;
    bit<16>   len;
    bit<16>   chksum;
}

header dns_t {
    bit<16>   id;
    bit<1>    qr;
    bit<4>    opcode;
    bit<1>    aa;
    bit<1>    tc;
    bit<1>    rd;
    bit<1>    ra;
    bit<1>    z;
    bit<1>    ad;
    bit<1>    cd;
    bit<4>    rcode;
    bit<16>   qdcount;
    bit<16>   ancount;
    bit<16>   nscount;
    bit<16>   arcount;
    bit<16> qname;
    bit<16> qtype;
    bit<16> qclass;
}

header lldp_t {
    bit<9> port;
    bit<7> padding;
}

/*@controller_header("packet_in")*/
header packet_in_t {
    bit<9> sport;
    bit<9> dport;
    bit<6> padding;
}


/*@controller_header("packet_out")*/
header packet_out_t {
    bit<9> egress_port;    
    bit<16> mcast;     
    bit<7> padding;
}

struct metadata {
    //bit<32>   meter_tag;
}

struct headers {
    packet_out_t packet_out;
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    udp_t        udp;
    dns_t        dns;
    lldp_t       lldp;
    packet_in_t  packet_in;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr, 
                inout metadata meta,
                inout standard_metadata_t standard_metadata
               ) {

    state start {
        transition select(standard_metadata.ingress_port){
            CPU_PORT: parse_pkt_out;// if is packect-out packet then extract packet-out header
            default: parse_ethernet;
        }
    }

    state parse_pkt_out{
        packet.extract(hdr.packet_out);
        transition accept;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4; 
            //TYPE_IPV6: parse_ipv6;
            TYPE_LLDP: parse_lldp;
            /*TYPE_PIN: parse_pkt_in;*/
            default: accept;
        }
    }

    /*state parse_pkt_in{*/
        /*packet.extract(hdr.packet_in);*/
        /*transition accept;*/
    /*}*/


    state parse_lldp {
        packet.extract(hdr.lldp);
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_UDP: parse_udp; 
            default: accept;
        }
    }
    state parse_udp {
        packet.extract(hdr.udp);
        packet.extract(hdr.dns);
        transition accept;
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata
                  ) {

    register<bit<32>>(NUM) reg_ingress;
    register<bit<32>>(512) r_reg; // record # of DNS response 
    register<bit<32>>(512) rq_reg; // record # of DNS reqest 
    register<bit<32>>(1) f_reg; // flag to determine if do project
    //meter(10, MeterType.packets) my_meter;
    meter(MAX_NUM, MeterType.bytes) ingress_meter_stats;
    MeterColor ingress_meter_output = MeterColor_GREEN;

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }


    action record_response(){
        bit<32> tmp;
        r_reg.read(tmp, (bit<32>)standard_metadata.ingress_port);
        r_reg.write((bit<32>)standard_metadata.ingress_port, tmp+1);
        r_reg.read(tmp, (bit<32>)standard_metadata.egress_spec);
        r_reg.write((bit<32>)standard_metadata.egress_spec, tmp+1);
    }
    
    table dns_response_record {
        key = { 
            hdr.dns.qr: exact;
        }
        actions = {
            record_response;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }

    action dns_request_hash_1(){
        bit<32> index;
        bit<32> tmp;
        index = (hdr.ipv4.srcAddr << 24) >> 24;
        index = index % 64;
        index = index << 10;
        index = index + ((bit<32>)hdr.dns.id % 1024);
        reg_ingress.read(tmp, index);
        reg_ingress.write(index, tmp+10);
    }

    table dns_request_hash_lpm{
        key = {
            hdr.dns.qr: exact;
        }
        actions = {
            dns_request_hash_1;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }
    
    /*action dns_response_hash_1(ip4Addr_t dstAddr, bit<16> id){*/
        /*bit<32> index;*/
        /*bit<32> tmp;*/
        /*index = (dstAddr << 24) >> 24;*/
        /*index = index % 64;*/
        /*index = index << 10;*/
        /*index = index + ((bit<32>)hdr.dns.id % 1024);*/
        /*ingress_meter_stats.execute_meter<MeterColor>((bit<32>) standard_metadata.ingress_port, ingress_meter_output);*/
    /*}*/

    /*table dns_response_hash_lpm{*/
        /*key = {*/
            /*hdr.ipv4.dstAddr: lpm;*/
            /*hdr.dns.id: exact;*/
        /*}*/
        /*actions = {*/
            /*dns_response_hash_1;*/
            /*NoAction;*/
        /*}*/
        /*size = 1024;*/
        /*default_action = NoAction;*/
    /*}*/

    action send_to_cpu(macAddr_t swAddr){
        standard_metadata.egress_spec = CPU_PORT;
        hdr.ethernet.dstAddr = swAddr;
        hdr.packet_in.setValid();
        /*hdr.ethernet.etherType = TYPE_LLDP;*/
        hdr.packet_in.sport = hdr.lldp.port;
        hdr.packet_in.dport = standard_metadata.ingress_port;
        /*hdr.lldp.setInvalid();*/
    }

    table pkt_in_table{
        key = {
            hdr.ethernet.etherType: exact;
        }
        actions = {
            send_to_cpu;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }

    action lldp_forward(macAddr_t swAddr){
        standard_metadata.egress_spec = hdr.packet_out.egress_port;
        /*hdr.packet_out.setInvalid();*/
        hdr.ethernet.setValid();
        hdr.lldp.setValid();
        hdr.ethernet.etherType = TYPE_LLDP;
        hdr.ethernet.srcAddr = swAddr;
        hdr.lldp.port = hdr.packet_out.egress_port;
    }

    action response_to_cpu(macAddr_t swAddr){
        standard_metadata.egress_spec = CPU_PORT;
        hdr.ethernet.setValid();
        hdr.ethernet.srcAddr = swAddr;
    }

    table pkt_out_table{
        key = {
            hdr.packet_out.padding: exact;
        }
        actions = {
            lldp_forward;
            response_to_cpu;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }

    apply {
        bit<32> index;
	bit<32> tmp;
        bit<32> flag;

        if (hdr.ipv4.isValid()) {
            if (hdr.dns.isValid()){ 

                f_reg.read(flag, 0);
                if (flag > 0){
                    if (hdr.dns.qr == 0){ //dns is request
                        dns_request_hash_lpm.apply();
                        ipv4_lpm.apply();
                    } else { //dns is response
                        /*dns_request_hash_lpm.apply()*/
                        ingress_meter_stats.execute_meter<MeterColor>((bit<32>) standard_metadata.ingress_port, ingress_meter_output);
                        index = (hdr.ipv4.dstAddr << 24) >> 24;
                        index = index % 64;
                        index = index << 10;
                        index = index + ((bit<32>)hdr.dns.id % 1024);
                        
                        reg_ingress.read(tmp, index);
                        if (tmp > 10){
                            reg_ingress.write(index, tmp - 10);
                            ipv4_lpm.apply();
                        } else if (tmp > 0){
                            reg_ingress.write(index, 0);
                            ipv4_lpm.apply();
                        } else if(ingress_meter_output == MeterColor_YELLOW) {
                            drop();
                        } else{
                            ipv4_lpm.apply();
                            
                        }
                    }
                } else {
                    ipv4_lpm.apply();
                }

                if(hdr.dns.qr == 1){
                    dns_response_record.apply();
                }else if(hdr.dns.qr == 0){
                    rq_reg.read(tmp, (bit<32>)standard_metadata.ingress_port);
                    rq_reg.write((bit<32>)standard_metadata.ingress_port, tmp+1);
                    rq_reg.read(tmp, (bit<32>)standard_metadata.egress_spec);
                    rq_reg.write((bit<32>)standard_metadata.egress_spec, tmp+1);
                }
            } else {
                /*ipv4_lpm.apply();*/
                drop();
            }
        } else if(hdr.lldp.isValid()){
            pkt_in_table.apply();
        } else if(hdr.packet_out.isValid()){
            pkt_out_table.apply();
        }
    }
}


/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata
                 ) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	      hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.dns);
        packet.emit(hdr.lldp);
        packet.emit(hdr.packet_in);
        //packet.emit(hdr.dns_qd);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
