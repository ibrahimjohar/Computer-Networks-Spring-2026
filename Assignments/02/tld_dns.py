#ibrahim johar farooqi - 23K-0074 - CN A2
from dns_message import DNSMessage

class TLDDNSServer:
    #this simulates a top-level domain (TLD) dns server
    #irl this is the server that is operated by organisations like
    #Verisign (.com/.net), PIR(.org), PKNIC(.pk) etc.
    
    #they know which authoritative dns servers are responsible for which specific domains
    
    def __init__(self):
        self.server_name = "a.gtld-servers.net"
        
        #TLD zone database
        #maps domain -> its authoritative nameservers(NS records)
        #irl this is maintained by domain registrars like GoDaddy, etc.
        
        self.authoritative_servers = {
            #.com domains
            "google.com": "ns1.google.com",
            "yahoo.com": "ns1.yahoo.com",
            "facebook.com": "a.ns.facebook.com",
            "github.com": "ns-421.awsdns-52.com",
            "amazon.com": "pdns1.ultradns.net",
            #.org domains
            "wikipedia.org": "ns0.wikimedia.org",
            #.net domains  
            "speedtest.net": "ns1.speedtest.net",
            #.pk domains
            "hec.gov.pk": "ns1.hec.gov.pk",
            "fast.edu.pk": "ns1.nu.edu.pk",
        }

    def resolve(self, query_msg):
        #receives a query msg, and returns a referral to the correct authoritative server for that domain
        #irl TLD server looks up whos responsible for this specific domain and points us there
        domain = query_msg.question
        print(f"\n[TLD DNS: {self.server_name}] received query for '{domain}'")
        
        #reply
        reply = DNSMessage(domain=domain, is_reply=True)
        reply.identification = query_msg.identification
        reply.is_authoritative = False
        reply.recursion_available = False
        
        if domain in self.authoritative_servers:
            auth_server = self.authoritative_servers[domain]
        else:
            #domain not in our registry, then generate a plausible nameserver name
            #e.g. "reddit.com" → "ns1.reddit.com"
            auth_server = f"ns1.{domain}"
            print(f"[TLD DNS] domain not in registry, assuming authoritative: '{auth_server}'")
        
        #TLD puts the referral in the authority section
        reply.add_authority("NS", auth_server, ttl=172800)          # 172800 = 2 days
        
        print(f"[TLD DNS] referring to authoritative server: '{auth_server}'")
        return reply, auth_server
