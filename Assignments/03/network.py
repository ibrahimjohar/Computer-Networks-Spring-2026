#ibrahim johar farooqi
#23K-0074
#BAI-6A
#CN - assignment 03

import copy
import hashlib
import random
import time
from config import LOSS_PROB, CORRUPT_PROB, DELAY_PROB, DELAY_MAX, PACKET_SIZE

#packet structure
class Packet:
    #represents a data or ACK packet
    def __init__(self, seq_num: int, data: bytes = b"", is_ack: bool = False):
        self.seq_num = seq_num
        self.data = data
        self.is_ack = is_ack
        self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        #MD5 over seq_num + data + is_ack
        content = f"{self.seq_num}{self.data}{self.is_ack}".encode()
        return hashlib.md5(content).hexdigest()

    def is_corrupt(self) -> bool:
        #compare stored checksum against freshly computed one
        return self.checksum != self._compute_checksum()

    def corrupt_packet(self):
        #simulate a bit-flip by mangling the stored checksum
        self.checksum = "CORRUPTED_XXXX"

    def __repr__(self):
        kind = "ACK" if self.is_ack else "DATA"
        return f"Packet({kind}, seq={self.seq_num}, data={self.data!r})"


#unreliable channel
class UnreliableChannel:
    #simulates an unreliable network channel; may randomly drop, corrupt, or delay packets
    def __init__(self, loss_prob=LOSS_PROB, corrupt_prob=CORRUPT_PROB, delay_prob=DELAY_PROB, delay_max=DELAY_MAX):
        self.loss_prob = loss_prob
        self.corrupt_prob = corrupt_prob
        self.delay_prob = delay_prob
        self.delay_max = delay_max
        self.stats = {"sent": 0, "lost": 0, "corrupted": 0, "delayed": 0}

    def transmit(self, packet: Packet) -> "Packet | None":
        #returns packet (possibly corrupted/delayed) or None (dropped)
        #works on a fresh copy so the original packet object is never mutated
        packet = copy.copy(packet)
        packet.checksum = packet._compute_checksum()    #restore valid checksum before mangling
        self.stats["sent"] += 1
        kind = "ACK" if packet.is_ack else "DATA"

        #01 - packet loss
        if random.random() < self.loss_prob:
            self.stats["lost"] += 1
            print(f"[CHANNEL] X {kind} seq={packet.seq_num} LOST")
            return None

        #02 - corruption
        if random.random() < self.corrupt_prob:
            self.stats["corrupted"] += 1
            packet.corrupt_packet()
            print(f"[CHANNEL] X {kind} seq={packet.seq_num} CORRUPTED")

        #03 - delay
        if random.random() < self.delay_prob:
            delay = random.uniform(0.01, self.delay_max)
            self.stats["delayed"] += 1
            print(f"[CHANNEL] {kind} seq={packet.seq_num} DELAYED {delay:.2f}s")
            time.sleep(delay)

        return packet

    def print_stats(self):
        s = self.stats
        print(f"\nChannel stats -> sent={s['sent']}, lost={s['lost']}, "
              f"corrupted={s['corrupted']}, delayed={s['delayed']}")


#helper: generate deterministic payload for a given sequence number
def make_data(seq_num: int, size: int = PACKET_SIZE) -> bytes:
    return f"PKT{seq_num:04d}".encode()[:size].ljust(size, b"_")