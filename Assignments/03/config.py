#configurable parameters
PACKET_COUNT = 10           #total packets to send
PACKET_SIZE = 8             #bytes of data per packet (payload)
WINDOW_SIZE = 4             #N for GBN and SR
TIMEOUT = 2.0               #seconds before retransmission
LOSS_PROB = 0.15            #probability a packet is lost     (0.0 – 1.0)
CORRUPT_PROB = 0.08         #probability a packet is corrupted (0.0 – 1.0)
DELAY_PROB = 0.10           #probability a packet is delayed   (0.0 – 1.0)
DELAY_MAX = 0.3             #max extra delay in seconds
RANDOM_SEED = 7             #fixed seed for reproducible runs; set to None for random