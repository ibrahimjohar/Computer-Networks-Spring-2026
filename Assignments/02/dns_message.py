#ibrahim johar farooqi - 23K-0074 - CN A2
import random

class DNSMessage:
    #this simulates the dns message (format from fig2). 
    #both queries and replies use this same structure.
    
    def __init__(self, domain=None, is_reply=False, recursion_required=True):
        #header section
        self.identification = random.randint(0, 65535)  #16-bit random id
        
        #flags (16 bits worth of info, stored as booleans)
        self.is_reply = is_reply                           #0 = query/question, 1 = reply
        self.recursion_required = recursion_required       #does the client want full recursive resolution?
        self.recursion_available = False
        self.is_authoritative = False
        
        #counts
        self.num_questions = 1 if domain else 0
        self.num_answer_rrs = 0
        self.num_authority_rrs = 0
        self.num_additional_rrs = 0
        
        #body sections
        self.question = domain                  #domain being asked abt (e.g. "google.com")
        self.answers = []                       #list of answer records (A, AAAA, CNAME, etc) 
        self.authority = []                     #NS records pointing to authoritative servers
        self.additional = []                    #extra info 
        
    def add_answer(self, record_type, value, ttl=300):
        #add a DNS record to the answer section
        self.answers.append({"type": record_type, "value": value, "ttl": ttl})
        self.num_answer_rrs += 1
    
    def add_authority(self, record_type, value, ttl=86400):
        #add a record to the authority section
        self.authority.append({"type": record_type, "value": value, "ttl": ttl})
        self.num_authority_rrs += 1
        
    def display(self):
        #print the DNS msg
        print(f"\n\n[DNS {'Reply' if self.is_reply else 'Query'}]")
        print(f"ID: {self.identification}")
        print(f"question: {self.question}")
        print(f"recursive: {self.recursion_required}")
        print(f"authoritative: {self.is_authoritative}")
        
        if self.answers:
            print("DNS information:")
            #grouping ans by record type
            grouped = {}
            
            for record in self.answers:
                grouped.setdefault(record["type"], []).append(f"{record["value"]} (TTL: {record['ttl']}s)")
            for rtype, values in grouped.items():
                print(f"  {rtype}: {', '.join(values)}")
                
        if self.authority:
            ns_values = [f"{r['value']} (TTL:{r['ttl']}s)" for r in self.authority]
            print(f"  NS (authority): {', '.join(ns_values)}")
