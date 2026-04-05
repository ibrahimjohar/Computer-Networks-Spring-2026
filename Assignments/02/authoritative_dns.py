#ibrahim johar farooqi - 23K-0074 - CN A2
#authoritative dns server - this is the server that confirms finally if it has 
#the answer to the query of not.
from dns_message import DNSMessage
import dns.resolver

class AuthoritativeDNSServer:
    #this simulates an authoritative dns server
    #irl this is the server that has the real/official records for a domain
    #like google runs ns1.google.com which holds the actual IP addresses for google.com
    #authoritative DNS doesnt ask anyone else for info, it just knows or not
    
    def __init__(self, server_name):
        self.server_name = server_name              #e.g. "ns1.google.com"
        
        #ttl -> time to live, how long the record is valid for
        #format: {"domain": {"record_type": [(value, TTL), ...]}}
        self.records = {
            "google.com": {
                "A": [("64.233.167.99", 300),
                          ("72.14.207.99", 300),
                          ("64.233.187.99", 300)],
                
                "AAAA": [("2607:f8b0:4004:c08::64", 300)],
                
                "NS": [("ns1.google.com.", 86400),
                          ("ns2.google.com.", 86400),
                          ("ns3.google.com.", 86400),
                          ("ns4.google.com.", 86400)],
                
                "MX": [("10 smtp1.google.com.", 3600),
                          ("10 smtp2.google.com.", 3600),
                          ("10 smtp3.google.com.", 3600),
                          ("10 smtp4.google.com.", 3600)],
            },

            "yahoo.com": {
                "A": [("72.30.35.9", 300),
                          ("72.30.35.10", 300),
                          ("98.137.246.7", 300),
                          ("98.138.219.231", 300)],
                
                "AAAA": [("2001:4998:58:1836::10", 300),
                          ("2001:4998:58:1836::11", 300)],
                
                "NS": [("ns1.yahoo.com.", 86400),
                          ("ns2.yahoo.com.", 86400),
                          ("ns3.yahoo.com.", 86400),
                          ("ns4.yahoo.com.", 86400),
                          ("ns5.yahoo.com.", 86400)],
                
                "MX": [("1 mta5.am0.yahoodns.net.", 3600),
                          ("1 mta6.am0.yahoodns.net.", 3600),
                          ("1 mta7.am0.yahoodns.net.", 3600)],
            },

            "facebook.com": {
                "A": [("157.240.241.35", 300),
                          ("157.240.229.35", 300)],
                
                "AAAA": [("2a03:2880:f12f:83:face:b00c:0:25de", 300)],
                
                "NS": [("a.ns.facebook.com.", 86400),
                          ("b.ns.facebook.com.", 86400),
                          ("c.ns.facebook.com.", 86400),
                          ("d.ns.facebook.com.", 86400)],
                
                "MX": [("10 smtpin.vvv.facebook.com.", 3600)],
            },

            "github.com": {
                "A": [("140.82.121.4", 300),
                          ("140.82.121.3", 300)],
                
                "NS": [("ns-1707.awsdns-21.co.uk.", 86400),
                          ("ns-421.awsdns-52.com.", 86400),
                          ("ns-520.awsdns-01.net.", 86400),
                          ("ns-1283.awsdns-32.org.", 86400)],
                
                "MX": [("1 aspmx.l.google.com.", 3600),
                          ("5 alt1.aspmx.l.google.com.", 3600)],
            },

            "amazon.com": {
                "A": [("205.251.242.103", 300),
                          ("52.94.236.248", 300),
                          ("54.239.28.85", 300)],
                
                "NS": [("pdns1.ultradns.net.", 86400),
                          ("pdns6.ultradns.co.uk.", 86400)],
                
                "MX": [("10 amazon-smtp.amazon.com.", 3600)],
            },
        }
        
    def resolve(self, query_msg):
        #receives a DNSMessage obj as query, looks up the domain, 
        #n then returns a DNSMessage reply
        domain = query_msg.question
        print(f"\n[Authoritative: {self.server_name}] received query for '{domain}")
        
        reply = DNSMessage(domain=domain, is_reply=True)
        reply.identification = query_msg.identification         #match the id
        reply.is_authoritative = True
        reply.recursion_available = False                       #authoritative servers dont recurse
        
        #check hardcoded records first
        if domain in self.records:
            records = self.records[domain]
            
            #add all the record types to the answer
            for record_type, values in records.items():
                for value, ttl in values:
                    reply.add_answer(record_type, value, ttl)
                    
            #the NS records also go into the authority section
            #irl this tells the client who authoritative server are
            if "NS" in records:
                for (ns_value, ttl) in records["NS"]:
                    reply.add_authority("NS", ns_value, ttl)
                    
            print(f"[Authoritative: {self.server_name}] returning {reply.num_answer_rrs} records (local zone)")
            return reply
        
        #domain not in hardcoded records - real DNS lookup
        print(f"[Authoritative: {self.server_name}] not in local zone, doing real DNS lookup...")
        found_any = False
        
        for record_type in ["A", "AAAA", "MX", "NS"]:
            try:
                answers = dns.resolver.resolve(domain, record_type, lifetime=3)
                for rdata in answers:
                    reply.add_answer(record_type, str(rdata), ttl=300)
                    if record_type == "NS":
                        reply.add_authority("NS", str(rdata), ttl=86400)
                found_any = True
            except Exception:
                pass    #this record type just doesnt exist for this domain, skip it
        
        if not found_any:
            print(f"[Authoritative: {self.server_name}] Error: no records found for '{domain}'")
            reply.error = f"no DNS record for '{domain}'"
        else:
            print(f"[Authoritative: {self.server_name}] returning {reply.num_answer_rrs} records (real lookup)")
        
        return reply        
    
    def knows_domain(self, domain):
        #does this server have records for this domain?
        return domain in self.records
