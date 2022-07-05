import pyshark

path_to_tshark = "C:\\Program Files\\Wireshark\\tshark.exe"

# iface_name = 'eth3'
filter_string = 'udp'

capture = pyshark.LiveCapture(
    # interface=iface_name,
    bpf_filter=filter_string
)

capture.sniff(timeout=5)
# capture

for packet in capture.sniff_continuously(packet_count=5):
    print('Just arrived:', packet)