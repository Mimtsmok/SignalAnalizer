import pyshark

path_to_tshark = "C:\\Program Files\\Wireshark\\tshark.exe"

iface_name = 'Ethernet 4'
filter_string = 'udp port 4163'

capture = pyshark.LiveCapture(
    interface=iface_name,
    # use_json=True,
    # include_raw=True
    bpf_filter=filter_string
)
# capture = pyshark.FileCapture('C:\\Users\\IMalakhov\\OneDrive - АО СИТРОНИКС\\Рабочий стол\\test2.pcap')

def get_packet_details(packet):
    protocol = packet.transport_layer
    source_address = packet.ip.src
    source_port = packet[packet.transport_layer].srcport
    destination_address = packet.ip.dst
    destination_port = packet[packet.transport_layer].dstport
    packet_time = packet.sniff_time
    data = packet.udp.payload.binary_value.decode()
    return f'Packet Timestamp: {packet_time}' \
           f'\nProtocol type: {protocol}' \
           f'\nSource address: {source_address}' \
           f'\nSource port: {source_port}' \
           f'\nDestination address: {destination_address}' \
           f'\nDestination port: {destination_port}' \
           f'\nData: {data}\n'

# capture.sniff(timeout=5)
# capture
for packet in capture.sniff_continuously():
# for packet in capture.sniff_continuously():
    # print('Just arrived:', packet)
    try:
        if "DATA" in str(packet.layers):
            print(get_packet_details(packet))
            # print(packet.data.data)
    except Exception as ex:
        print(ex)

# import psutil


# def getInterfaces():
#     addrs = psutil.net_if_addrs()
#     return addrs.keys()

# print(getInterfaces())