#ibrahim johar farooqi
#23K-0074
#BAI-6A
#CN - assignment 03

import random
import time
import config
from network import UnreliableChannel
from rdt30 import RDT30
from gbn import GoBackN
from sr import SelectiveRepeat

#test scenario definitions
#each scenario overrides channel probabilities to isolate a specific failure type
SCENARIOS = {
    "1": {
        "name": "No errors (ideal channel)",
        "loss": 0.0, "corrupt": 0.0, "delay": 0.0
    },
    "2": {
        "name": "Packet loss only",
        "loss": 0.3, "corrupt": 0.0, "delay": 0.0
    },
    "3": {
        "name": "Corruption only",
        "loss": 0.0, "corrupt": 0.3, "delay": 0.0
    },
    "4": {
        "name": "Delayed packets only",
        "loss": 0.0, "corrupt": 0.0, "delay": 0.5
    },
    "5": {
        "name": "All errors (loss + corruption + delay)",
        "loss": config.LOSS_PROB, "corrupt": config.CORRUPT_PROB, "delay": config.DELAY_PROB
    },
}


def make_channel(scenario: dict) -> UnreliableChannel:
    #build a channel configured for the chosen test scenario
    return UnreliableChannel(
        loss_prob = scenario["loss"],
        corrupt_prob = scenario["corrupt"],
        delay_prob = scenario["delay"],
        delay_max = config.DELAY_MAX,
    )


def print_banner():
    print("""
CN A03 - Reliable Data Transfer Protocols --- rdt 3.0  |  Go-Back-N  |  Selective Repeat
\n
  Config:
    Packets      : {pkt}
    Packet size  : {sz} bytes
    Window size  : {win}
    Timeout      : {to}s
    Loss prob    : {lp:.0%}
    Corrupt prob : {cp:.0%}
    Delay prob   : {dp:.0%}
""".format(
        pkt=config.PACKET_COUNT, sz=config.PACKET_SIZE, win=config.WINDOW_SIZE,
        to=config.TIMEOUT, lp=config.LOSS_PROB, cp=config.CORRUPT_PROB, dp=config.DELAY_PROB
    ))


def pick_protocol() -> str:
    print("Choose protocol:")
    print("1. rdt 3.0  (Stop-and-Wait)")
    print("2. Go-Back-N")
    print("3. Selective Repeat")
    print("4. Run all three")
    return input("\nEnter choice [1-4]: ").strip()


def pick_scenario() -> dict:
    print("\nChoose test scenario:")
    for key, s in SCENARIOS.items():
        print(f"  {key}. {s['name']}")
    choice = input("\nEnter scenario [1-5]: ").strip()
    if choice not in SCENARIOS:
        print("Invalid scenario -- using default (all errors)")
        return SCENARIOS["5"]
    scenario = SCENARIOS[choice]
    print(f"\n[TEST] Running: {scenario['name']}")
    return scenario


def run_protocol(choice: str, channel: UnreliableChannel):
    #instantiate the chosen protocol with the pre-configured channel
    if choice == "1":
        RDT30(channel=channel).run()
    elif choice == "2":
        GoBackN(channel=channel).run()
    elif choice == "3":
        SelectiveRepeat(channel=channel).run()
    elif choice == "4":
        #each protocol gets its own fresh channel so stats are independent
        sep = "\n" + "-" * 55
        sc  = {
            "loss":    channel.loss_prob,
            "corrupt": channel.corrupt_prob,
            "delay":   channel.delay_prob,
        }
        RDT30(channel=make_channel(sc)).run()
        print(sep)
        GoBackN(channel=make_channel(sc)).run()
        print(sep)
        SelectiveRepeat(channel=make_channel(sc)).run()
    else:
        print("Invalid protocol choice.")


def main():
    if config.RANDOM_SEED is not None:
        random.seed(config.RANDOM_SEED)

    print_banner()

    protocol = pick_protocol()
    scenario = pick_scenario()
    channel  = make_channel(scenario)

    start = time.time()
    run_protocol(protocol, channel)
    elapsed = time.time() - start

    print(f"\nTotal simulation time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()