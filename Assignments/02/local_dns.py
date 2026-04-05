#ibrahim johar farooqi - 23K-0074 - CN A2
import time
from dns_message import DNSMessage
from root_dns import RootDNSServer
from tld_dns import TLDDNSServer
from authoritative_dns import AuthoritativeDNSServer

class LocalDNSServer:
    #this simulates a local dns server (recursive resolver)
    #irl this the ISP's DNS server/or a public one like google's 8.8.8.8
    #computer only talks to local dns
    #local dns then handles contacting root, tld, authoritative servers 
    #as needed to resolve the query
    
    #max num of entries in cache (kept small for demo purpose)
    CACHE_MAX_SIZE = 5
    
    def __init__(self, server_name="dns.local.isp.net"):
        self.server_name = server_name
        #cache format: {"domain": {"answers": [...], "expires_at": float}}
        #irl the local dns caches the answers based on TTL
        #expires_at = time.time() + TTL
        #when time.time() > expires_at, the record is expired
        
        self.cache = {}
        #local dns talks to the following servers
        self.root_server = RootDNSServer()
        self.tld_server = TLDDNSServer()
        self.auth_server = AuthoritativeDNSServer("ns1.google.com")
        
        #tracking cache hits/misses
        self.cache_hits = 0
        self.cache_misses = 0
        
    def resolve(self, domain):
        #main resolution method - called by the client
        #irl computer sends a UDP packet to this server
        #then this server checks cache, then resolves if needed
        
        print(f"\n{'='*60}")
        print(f"[Local DNS: {self.server_name}]")
        print(f"Received query for '{domain}'")
        
        query = DNSMessage(domain=domain)
        
        #check cache first(step 1)
        cached = self.check_cache(domain)
        if cached:
            print(f"Cache Hit! - returning cached response")
            self.cache_hits += 1
            cached.display()
            return cached
        
        self.cache_misses += 1
        print(f"Cache Miss - need to resolve (starting recursive resolution)")
        
        #recursive resolution, {root->tld->authoritative} (step 2)
        reply = self.recursive_resolve(query)
        
        #cache the result, if we got a valid ans (step 3)
        if reply and hasattr(reply, "answers") and reply.answers:
            self.cache_result(domain, reply)
            
        if reply:
            reply.display()
            
        return reply
    
    def recursive_resolve(self, query):
        #goes up the hierarchy: root -> tld -> authoritative
        #irl it contacts multiple servers on the client's behalf
        #and only returns when it has the final answer
        
        domain = query.question
        
        #ask root dns (stage 1)
        print(f"\n[Stage 01]...contacting Root DNS server...")
        root_reply, tld_server_name = self.root_server.resolve(query)
        
        if tld_server_name is None:
            print(f"error: root DNS couldnt find TLD for '{domain}'")
            return root_reply
        
        #ask TLD dns (stage 2)
        print(f"\n[Stage 02]...contacting the TLD DNS server ({tld_server_name})...")
        tld_reply, auth_server_name = self.tld_server.resolve(query)
        
        if auth_server_name is None:
            print(f"error: TLD DNS has no authoritative server for '{domain}'")
            return tld_reply
        
        #ask authoritative DNS
        print(f"\n[Stage 03]...contacting Authoritative DNS server ({auth_server_name})...")
        self.auth_server.server_name = auth_server_name            #update authoritative server instance to match the referral
        auth_reply = self.auth_server.resolve(query)
        
        if not auth_reply.answers:
            print(f"error: authoritative DNS has no records for '{domain}'")
            
        return auth_reply
    
    def check_cache(self, domain):
        #check if we have a valid (not expired) cached entry
        #irl every cached record has a TTL, and once that TTL expires,
        #the record must be fetched fresh from the authoritative server
        if domain not in self.cache:
            return None
        
        entry = self.cache[domain]
        
        #check if expired
        if time.time() > entry["expires_at"]:
            print(f"cached entry for '{domain}' has expired - removing now...")
            del self.cache[domain]
            return None
        
        reply = DNSMessage(domain=domain, is_reply=True)
        reply.is_authoritative = False                  #cached answers are NOT authoritative
        reply.answers = entry["answers"]
        reply.authority = entry["authority"]
        reply.num_answer_rrs = len(reply.answers)

        time_left = int(entry["expires_at"] - time.time())
        print(f"cached entry valid - {time_left}s remaining on TTL")

        return reply
    
    def cache_result(self, domain, reply):
        #find min TTL among all answer records
        ttls = [r["ttl"] for r in reply.answers if "ttl" in r]
        min_ttl = min(ttls) if ttls else 300
        
        #AUTO-FLUSH: if cache is full, remove the oldest entry (LRU)
        #irl resolvers do this instead of wiping everything
        if len(self.cache) >= self.CACHE_MAX_SIZE:
            oldest_domain = next(iter(self.cache))              #first inserted = oldest
            del self.cache[oldest_domain]
            print(f"\nCache full - removed oldest entry: '{oldest_domain}'")

        self.cache[domain] = {
            "answers": reply.answers,
            "authority": reply.authority,
            "expires_at": time.time() + min_ttl,
            "cached_at": time.time(),
        }
        print(f"\nCached '{domain}' for {min_ttl} seconds")
    
    def show_cache(self):
        print(f"\n{'='*60}")
        print(f"Cache Status ({len(self.cache)}/{self.CACHE_MAX_SIZE} entries)")
        print(f"Hits: {self.cache_hits} | Misses: {self.cache_misses}")
        print(f"{'='*60}")
        
        if not self.cache:
            print("Cache is empty.")
            return
        
        for domain, entry in self.cache.items():
            time_left = int(entry["expires_at"] - time.time())
            status = "valid" if time_left > 0 else "expired"
            print(f"\nDomain: {domain}")
            print(f"Status: {status} ({time_left}s remaining)")
            grouped = {}
            for r in entry["answers"]:
                grouped.setdefault(r["type"], []).append(r["value"])
            for rtype, vals in grouped.items():
                print(f"{rtype:10}: {','.join(vals)}")
        
    
    
