#ibrahim johar farooqi - 23K-0074 - CN A2
from local_dns import LocalDNSServer

def print_menu():
    print("\n-----------------------------------------")
    print("DNS Simulator")
    print("-----------------------------------------")
    print("1. Lookup a domain")
    print("2. Show cache")
    print("3. Clear cache manually")
    print("4. Demo: show caching in action")
    print("5. Demo: show auto-flush")
    print("6. Exit")
    print("-----------------------------------------")

def demo_caching(local):
    print("\n>>> DEMO: Caching")
    print("Querying google.com twice.")
    print("First should do full resolution, second should hit cache.\n")
    input("Press Enter to send first query...")
    local.resolve("google.com")
    input("\nPress Enter to send second query (same domain)...")
    local.resolve("google.com")
    print("\nNotice:")
    print("  - second query skipped Root/TLD/Authoritative entirely")
    print("  - 'authoritative: False' on cached reply (its a copy, not from original server)")

def demo_autoflush(local):
    print("\n>>> DEMO: LRU Cache Eviction")
    print(f"Cache limit is {local.CACHE_MAX_SIZE} entries.")
    print("When full, the oldest entry gets removed to make room.\n")

    domains = ["google.com", "yahoo.com", "facebook.com", "github.com", "amazon.com", "reddit.com"]

    for domain in domains:
        input(f"Press Enter to query '{domain}'...")
        local.resolve(domain)
        local.show_cache()
        print(f"  Current cache size: {len(local.cache)}/{local.CACHE_MAX_SIZE}")

    print("\nNotice:")
    print("  - cache never exceeded the limit")
    print("  - oldest entry was dropped each time a new one came in")
    print("  - dropped entries would need full resolution again if queried")

def main():
    print("\nStarting DNS Simulator...")
    local = LocalDNSServer()
    print(f"Local DNS Server: {local.server_name}")
    print(f"Cache size limit: {local.CACHE_MAX_SIZE} entries")

    while True:
        print_menu()
        choice = input("Enter choice: ").strip()

        if choice == "1":
            domain = input("Enter domain (e.g. google.com): ").strip()
            if not domain:
                print("No domain entered.")
                continue
            local.resolve(domain)

        elif choice == "2":
            local.show_cache()

        elif choice == "3":
            confirm = input("Clear entire cache? (y/n): ").strip().lower()
            if confirm == "y":
                count = len(local.cache)
                local.cache.clear()
                print(f"Cache cleared. ({count} entries removed)")
            else:
                print("Cancelled.")

        elif choice == "4":
            demo_caching(local)      #cache state carries over

        elif choice == "5":
            demo_autoflush(local)    #cache state carries over

        elif choice == "6":
            print("Exiting.")
            break

        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
