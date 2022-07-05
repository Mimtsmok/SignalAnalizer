import scapy
print(scapy.VERSION)
try:
    from scapy.all import *
    sniffer = sniff(count=100, lfilter=lambda x: x.haslayer('UDP')) # and x['UDP'].sport==4163)
    print(sniffer.hexdump())
except Exception as ex:
    print(ex)
    input("...")
input("...")