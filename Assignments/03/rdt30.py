#ibrahim johar farooqi
#23K-0074
#BAI-6A
#CN - assignment 03

import time
from config import PACKET_COUNT, TIMEOUT
from network import Packet, UnreliableChannel, make_data

#protocol 01 - rdt 3.0 (stop-and-wait)
class RDT30:
    #sender FSM states: WAIT_FOR_CALL | WAIT_FOR_ACK
    #receiver FSM states: WAIT_FOR_0 | WAIT_FOR_1
    #sequence numbers alternate between 0 and 1 (alternating-bit protocol)

    def __init__(self, total_packets=PACKET_COUNT, timeout=TIMEOUT, channel: UnreliableChannel = None):
        self.total_packets = total_packets
        self.timeout = timeout
        #allow an externally configured channel (used by test scenarios)
        self.channel = channel if channel else UnreliableChannel()

    #SENDER
    def sender(self):
        print("\n" + "-" * 55)
        print("rdt 3.0  SENDER  started  (Stop-and-Wait)")
        print("-" * 55)

        seq = 0     #alternating bit: 0 or 1
        sent_count = 0
        retransmissions = 0

        while sent_count < self.total_packets:
            data = make_data(sent_count)
            packet = Packet(seq, data)

            #keep retrying until a correct ACK is received (STATE: WAIT_FOR_CALL)
            while True:
                print(f"\n[SENDER] Sending seq={seq}  data={data!r}")
                ack = self._send_and_wait(packet)

                #STATE: WAIT_FOR_ACK
                if ack is None:
                    print(f"[SENDER] - TIMEOUT -- retransmitting seq={seq}")
                    retransmissions += 1
                elif ack.is_corrupt():
                    print(f"[SENDER] X Corrupt ACK -- retransmitting seq={seq}")
                    retransmissions += 1
                elif ack.seq_num != seq:
                    print(f"[SENDER] X Wrong ACK (got {ack.seq_num}, want {seq}) -- retransmit")
                    retransmissions += 1
                else:
                    print(f"[SENDER] ✓ ACK {seq} received -- moving on")
                    break       #correct ACK received -> exit retry loop

            seq = 1 - seq       #flip alternating bit
            sent_count += 1

        print(f"\n[SENDER] All {self.total_packets} packets delivered.")
        print(f"[SENDER] Total retransmissions: {retransmissions}")
        self.channel.print_stats()

    def _send_and_wait(self, packet: Packet) -> "Packet | None":
        #send packet through unreliable channel and wait up to TIMEOUT for ACK
        delivered = self.channel.transmit(packet)
        if delivered is None:
            time.sleep(self.timeout)    #wait full timeout if packet was lost
            return None                 #signal retransmit to caller

        #simulate receiver processing and get back an ACK
        ack = self._receiver_fsm(delivered)

        #ACK travels back through the same unreliable channel
        if ack:
            ack = self.channel.transmit(ack)
        return ack

    #RECEIVER FSM
    def _receiver_fsm(self, packet: Packet) -> "Packet | None":
        #WAIT_FOR_0: expects seq 0, sends ACK 0 if correct
        #WAIT_FOR_1: expects seq 1, sends ACK 1 if correct
        #on corruption: sends ACK for the opposite seq (acts as NAK)
        if packet is None:
            return None

        if packet.is_corrupt():
            print(f"[RECEIVER] X Corrupt packet -- sending NAK (ACK for other seq)")
            #ACK for opposite sequence number acts as a negative acknowledgement
            return Packet(1 - packet.seq_num, is_ack=True)

        print(f"[RECEIVER] ✓ Received seq={packet.seq_num}  data={packet.data!r}")
        return Packet(packet.seq_num, is_ack=True)

    def run(self):
        self.sender()