import socket
from scapy.all import *

class Capture:
	"""The capture object keeps captures packets from a given network interface and processes them"""

	def __init__(self, iface):
		"""Initializes the capture object with a given network interface on which packets should be captured"""
		
		self.iface = iface

	def padding(self, data):
		"""Padds the pair of src and dst address so that it is exactly 64 bytes long"""

		if len(data) > 64:
			raise error("Data exceeds packet length")

		data = data + "@"
		while len(data) < 64:
			data = data + "0"
		
		return data

	def callback(self, packet):
		"""The callback routine for each packet

		This is called on each new packet that is collected. Here we update the evidence with the data collected from the new packet.
		"""

		src = packet[IP].src
		dst = packet[IP].dst

		if TCP in packet:
			src_port = packet[TCP].sport
			dst_port = packet[TCP].dport
		elif UDP in packet:
			src_port = packet[UDP].sport
			dst_port = packet[UDP].dport
		else:
			src_port = "other"
			dst_port = "other"

		data = src + ":" + str(src_port) + "-" + dst + ":" + str(dst_port)
		data = self.padding(data)
		sock.send(data.encode())

	def capture(self, subnet, n=100):
		"""Captures n packets (100 by default) and applies the callback function to each of them"""

		capture_filter = "ip and src net " + subnet
		packets = sniff(iface=self.iface, prn=self.callback, count=n, filter=capture_filter, store=0)
		wrpcap("sniff.pcap", packets)

# Create a connection to the server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#host = input("Server IP address: ")
#port = input("Server port: ")
#subnet = input("Subnet: ")
host = "10.132.0.2"
port = "8888"
subnet = "10.132.0.0/28"
sock.connect((host,int(port)))
print("Connected...")
# Capture packets indefinitely, callback function will send them to the server
c = Capture("eth0")
c.capture(subnet, 0)
