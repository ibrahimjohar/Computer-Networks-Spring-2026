#ibrahim johar farooqi - 23K-0074 - CN A2
from dns_message import DNSMessage

class RootDNSServer:
    #this simulates a root dns server
    #irl there are 13 root servers in the world,
    #they only know one thing that is which TLD server handles which top level domain (e.g. .com, .org, .net, etc)
    #they dont know the actual IP addresses of websites
    
    def __init__(self):
        self.server_name = "root-server.net"
        #root zone database
        #maps TLD extensions -> TLD server responsible for them
        #irl there are the actual TLD servers that IANA delegates to
        
        self.tld_servers = {
            "com": "a.gtld-servers.net",          #handles all .com domains
            "org": "b0.org.afilias-nst.org",
            "net": "a.gtld-servers.net",          #.net shares with .com
            "edu": "a.edu-servers.net",
            "gov": "a.gov-servers.net",
            "pk": "ns1.pknic.net.pk",            #pakistan's TLD server
            "io": "a0.nic.io",
            "co": "ns1.nic.co",
        }
        
    def resolve(self, query_msg):
        #receives a query msg, extracts the TLD, & returns the a referral to the correct TLD server
        #irl root server reads the rightmost part of the domain (e.g. "com" from "google.com") & replies with
        #the address of the TLD server for that extension.
        
        domain = query_msg.question
        tld = domain.split(".")[-1]           #"google.com" → "com"
        
        print(f"\n[Root DNS] received query for '{domain}'")
        print(f"[Root DNS] extracted TLD: '.{tld}'")
        
        #build reply, same ID as query
        reply = DNSMessage(domain=domain, is_reply=True)
        reply.identification = query_msg.identification
        reply.is_authoritative = False                      #root is NOT authoritative for the domain
        reply.recursion_available = False                   #root doesn't recurse
        
        if tld not in self.tld_servers:
            print(f"[Root DNS] Error: unknown TLD '.{tld}")
            reply.error = f"unknown TLD '.{tld}"
            return reply, None
        
        tld_server = self.tld_servers[tld]
        
        #root puts the referral in the authority section
        reply.add_authority("NS", tld_server, ttl=518400)    #518400 = 6 days (root referrals are cached for a long time)
        return reply, tld_server
        
    
