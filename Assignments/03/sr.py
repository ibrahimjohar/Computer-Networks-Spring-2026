#ibrahim johar farooqi
#23K-0074
#BAI-6A
#CN - assignment 03

import threading
import time
from config import PACKET_COUNT, WINDOW_SIZE, TIMEOUT
from network import Packet, UnreliableChannel, make_data

#protocol 03 - selective repeat (SR)
class SelectiveRepeat:
    #sender FSM:
    #  - maintains sliding window [base, base+N)
    #  - individual timer per unacknowledged packet
    #  - on timeout for packet i: retransmit ONLY packet i (not the whole window)
    #receiver FSM:
    #  - accepts any packet within [recv_base, recv_base+N)
    #  - buffers out-of-order packets until the gap is filled
    #  - sends individual ACK for each correctly received packet
    #  - delivers buffered packets in-order to upper layer once gap closes

    def __init__(self, total_packets=PACKET_COUNT, window_size=WINDOW_SIZE, timeout=TIMEOUT, channel: UnreliableChannel = None):
        self.total_packets = total_packets
        self.N = window_size
        self.timeout = timeout
        #allow an externally configured channel (used by test scenarios)
        self.channel = channel if channel else UnreliableChannel()

        #receiver state
        self._recv_buffer = {}              #seq_num -> Packet (buffered out-of-order)
        self._recv_base = 0              #start of receiver window
        self._recv_lock = threading.Lock()

        #ACK queue (receiver -> sender)
        self._ack_queue = []
        self._ack_lock = threading.Lock()

    #SENDER
    def run(self):
        print("\n" + "-" * 55)
        print(f"Selective Repeat  SENDER  (N={self.N})")
        print("-" * 55)

        base = 0
        next_seq = 0
        retransmit = 0

        #per-packet tracking arrays
        acked = [False] * self.total_packets  #True once ACK received
        timer_start = [None]  * self.total_packets  #individual timer per packet
        all_packets = [Packet(i, make_data(i)) for i in range(self.total_packets)]

        while base < self.total_packets:

            #fill the window with new packets
            while next_seq < self.total_packets and next_seq < base + self.N:
                pkt = all_packets[next_seq]
                print(f"\n[SENDER] Sending seq={next_seq}  "
                      f"(window: {base}–{min(base+self.N-1, self.total_packets-1)})")
                self._send_packet(pkt)
                timer_start[next_seq] = time.time()     #start individual timer
                next_seq += 1

            #process one incoming ACK (individual, not cumulative)
            ack = self._get_ack()
            if ack and not ack.is_corrupt():
                sn = ack.seq_num
                if base <= sn < base + self.N and not acked[sn]:
                    print(f"[SENDER] ✓ Individual ACK {sn}")
                    acked[sn] = True
                    timer_start[sn] = None              #cancel this packet's timer
                    #slide the window forward over all consecutively ACKed packets
                    while base < self.total_packets and acked[base]:
                        base += 1
            elif ack and ack.is_corrupt():
                print(f"[SENDER] X Corrupt ACK -- ignored")

            #per-packet timeout: only retransmit the specific timed-out packet
            now = time.time()
            for i in range(base, min(next_seq, self.total_packets)):
                if not acked[i] and timer_start[i] and (now - timer_start[i]) > self.timeout:
                    print(f"\n[SENDER] TIMEOUT for seq={i} -- SR: retransmitting ONLY seq={i}")
                    self._send_packet(all_packets[i])
                    timer_start[i] = time.time()        #restart this packet's timer
                    retransmit += 1

            time.sleep(0.05)    #small yield to avoid busy-wait

        print(f"\n[SENDER] All {self.total_packets} packets delivered.")
        print(f"[SENDER] Total retransmissions: {retransmit}")
        self.channel.print_stats()

    def _send_packet(self, packet: Packet):
        #deliver packet through unreliable channel to receiver and collect the ACK
        delivered = self.channel.transmit(packet)
        ack = None
        if delivered:
            ack = self._receiver_fsm(delivered)
        if ack:
            ack = self.channel.transmit(ack)    #ACK also travels through unreliable channel
        if ack:
            with self._ack_lock:
                self._ack_queue.append(ack)

    #RECEIVER FSM
    def _receiver_fsm(self, packet: Packet) -> "Packet | None":
        #SR receiver FSM:
        #  - accepts any packet in [recv_base, recv_base+N)
        #  - buffers out-of-order packets
        #  - delivers buffered data in-order to upper layer when gap is filled
        with self._recv_lock:
            if packet.is_corrupt():
                print(f"[RECEIVER] X Corrupt packet seq={packet.seq_num} -- discarded (no ACK)")
                return None     #SR receiver sends no ACK for corrupt packets

            sn = packet.seq_num

            #within receiver window -> accept and buffer
            if self._recv_base <= sn < self._recv_base + self.N:
                if sn not in self._recv_buffer:
                    self._recv_buffer[sn] = packet
                    print(f"[RECEIVER] ✓ Buffered seq={sn}")
                else:
                    print(f"[RECEIVER] (duplicate seq={sn} -- already buffered)")

                #deliver all consecutive packets starting from recv_base to upper layer
                while self._recv_base in self._recv_buffer:
                    delivered_pkt = self._recv_buffer.pop(self._recv_base)
                    print(f"[RECEIVER] ^ Delivered seq={self._recv_base}"
                          f"  data={delivered_pkt.data!r}  to upper layer")
                    self._recv_base += 1

                return Packet(sn, is_ack=True)   #individual ACK for this specific packet

            #below window: already delivered, re-ACK so sender can advance
            elif sn < self._recv_base:
                print(f"[RECEIVER] (old packet seq={sn} -- re-ACKing)")
                return Packet(sn, is_ack=True)

            #above window: too far ahead, discard
            else:
                print(f"[RECEIVER] X Packet seq={sn} outside window -- discarded")
                return None

    def _get_ack(self) -> "Packet | None":
        with self._ack_lock:
            if self._ack_queue:
                return self._ack_queue.pop(0)
        return None