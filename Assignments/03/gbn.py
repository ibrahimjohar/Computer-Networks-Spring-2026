#ibrahim johar farooqi
#23K-0074
#BAI-6A
#CN - assignment 03

import threading
import time
from config import PACKET_COUNT, WINDOW_SIZE, TIMEOUT
from network import Packet, UnreliableChannel, make_data


#protocol 02 - go-back-n (GBN)
class GoBackN:
    #sender FSM:
    #  - maintains sliding window [base, base+N)
    #  - on timeout: retransmit ALL unacknowledged packets in the window
    #  - on corrupt/wrong ACK: ignore (wait for timeout)
    #receiver FSM:
    #  - accepts ONLY the next expected in-order packet
    #  - discards out-of-order packets and re-sends last good cumulative ACK

    def __init__(self, total_packets=PACKET_COUNT, window_size=WINDOW_SIZE, timeout=TIMEOUT, channel: UnreliableChannel = None):
        self.total_packets = total_packets
        self.N = window_size
        self.timeout = timeout
        #allow an externally configured channel (used by test scenarios)
        self.channel = channel if channel else UnreliableChannel()

        #shared state between sender and receiver (simulated pipeline)
        self._lock = threading.Lock()
        self._ack_buffer = []   #ACKs queued by receiver, consumed by sender
        self._recv_seq = 0    #receiver's next expected sequence number

    #SENDER
    def run(self):
        print("\n" + "-" * 55)
        print(f"Go-Back-N  SENDER  (N={self.N})")
        print("-" * 55)

        base = 0     #oldest unacknowledged packet
        next_seq = 0     #next sequence number to send
        retransmit = 0
        window = {}    #seq_num -> Packet (currently in-flight)
        all_packets = [Packet(i, make_data(i)) for i in range(self.total_packets)]
        timer_start = None  #single timer covers the entire window

        while base < self.total_packets:

            #fill the window with new packets up to size N
            while next_seq < self.total_packets and next_seq < base + self.N:
                pkt = all_packets[next_seq]
                window[next_seq] = pkt
                print(f"\n[SENDER] Sending seq={next_seq}  (window: {base}–{base+self.N-1})")
                self._deliver_to_receiver(pkt)
                if timer_start is None:
                    timer_start = time.time()   #start timer on first unACKed packet
                next_seq += 1

            #check for incoming ACKs (cumulative)
            ack = self._get_ack()
            if ack and not ack.is_corrupt():
                if base <= ack.seq_num < base + self.N:
                    print(f"[SENDER] ✓ Cumulative ACK {ack.seq_num} received")
                    base = ack.seq_num + 1
                    if base == next_seq:
                        timer_start = None          #all packets ACKed -> stop timer
                    else:
                        timer_start = time.time()   #restart timer for remaining window
                else:
                    print(f"[SENDER] (duplicate/old ACK {ack.seq_num} -- ignored)")
            elif ack and ack.is_corrupt():
                print(f"[SENDER] X Corrupt ACK -- ignored")

            #timeout check: go back and retransmit entire window from base
            if timer_start and (time.time() - timer_start) > self.timeout:
                print(f"\n[SENDER] TIMEOUT -- Go-Back-N: retransmitting {base}..{next_seq-1}")
                retransmit += (next_seq - base)
                for i in range(base, next_seq):
                    self._deliver_to_receiver(all_packets[i])
                timer_start = time.time()   #restart timer after retransmission

            time.sleep(0.05)    #small yield to avoid busy-wait

        print(f"\n[SENDER] All {self.total_packets} packets delivered.")
        print(f"[SENDER] Total retransmissions: {retransmit}")
        self.channel.print_stats()

    def _deliver_to_receiver(self, packet: Packet):
        #pass packet through unreliable channel to receiver and collect the ACK
        delivered = self.channel.transmit(packet)
        ack = None
        if delivered:
            ack = self._receiver_fsm(delivered)
        if ack:
            ack = self.channel.transmit(ack)    #ACK also travels through unreliable channel
        if ack:
            with self._lock:
                self._ack_buffer.append(ack)

    #RECEIVER FSM
    def _receiver_fsm(self, packet: Packet) -> "Packet | None":
        #GBN receiver FSM:
        #  - accepts only the next expected in-order packet
        #  - sends cumulative ACK for the last correctly received in-order packet
        #  - discards everything else and re-sends the last good ACK

        if packet.is_corrupt():
            print(f"[RECEIVER] X Corrupt packet seq={packet.seq_num} -- discarded")
            #re-send last good cumulative ACK so sender knows where receiver is
            if self._recv_seq > 0:
                return Packet(self._recv_seq - 1, is_ack=True)
            return None

        if packet.seq_num == self._recv_seq:
            print(f"[RECEIVER] ✓ In-order seq={packet.seq_num} accepted")
            ack = Packet(self._recv_seq, is_ack=True)
            self._recv_seq += 1
            return ack
        else:
            print(f"[RECEIVER] X Out-of-order seq={packet.seq_num}"
                  f" (expected {self._recv_seq}) -- discarded")
            #re-send last cumulative ACK
            if self._recv_seq > 0:
                return Packet(self._recv_seq - 1, is_ack=True)
            return None

    def _get_ack(self) -> "Packet | None":
        with self._lock:
            if self._ack_buffer:
                return self._ack_buffer.pop(0)
        return None