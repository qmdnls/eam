import numpy as np
import py2neo as neo
import signal
import socket
import threading
import ipaddress

class HMM:
	"""A Hidden Markov Model that will be used to keep track of uncertainty in the network

	This object stores the prior probability p that a host exists at a given network address.
	"""

	def add_evidence(self):
		"""Call this if evidence has been observed. Sets a variable so forward algorithm can update the HMM accordingly."""
		self.e = 1

	def update(self):
		"""Updates the HMM by one step using the forward algorithm"""

		# Update p according to the transition model
		self.p = self.transition_model * self.p + (1 - self.transition_model) * (1 - self.p)
		
		# Now factor in evidence and normalize to [0,1)
		if self.e:
			self.p = self.sensor_model * self.p
		else:
			self.p = (1 - self.sensor_model) * self.p
	
		# Normalize
		self.p /= np.sum(self.p)
		
		# Reset the evidence
		self.e = 0

	def __init__(self, transition_model=0.95, sensor_model=[0.7,0.1]):
		self.transition_model = transition_model
		self.sensor_model = np.array(sensor_model)
		self.p = np.array([0.5, 0.5])
		self.e = 0

class Hosts:
	"""This object keeps track of host-HMM-pairs and provides add and update with evidence functions.

	Internally this adds a dictionary entry for every host using its network address tuple (IP + port, i.e. (3.3.3.3, 21)) as key and the corresponding HMM as the value. Evidence can be added for the current time slice. All hosts can then be updated using the forward algorithm given the evidence that has been added thus far. 
	"""
	
	def add_host(self, addr, port):
		"""Creates a HMM for a new host if it doesn't exist yet and adds the host-HMM-pair to the dictionary"""
		if (addr, port) not in self.hosts:
			self.hosts[(addr, port)] = HMM()

	def add_connection(self, src_addr, src_port, dst_addr, dst_port):
		"""Creates a HMM for a connection, a tuple of two addresses, and adds it to the dictionary of HMMs"""
		if ((src_addr, src_port), (dst_addr, dst_port)) not in self.connections:
			self.connections[((src_addr, src_port), (dst_addr, dst_port))] = HMM()

	def add_evidence(self, addr, port, dst_addr=None, dst_port=None):
		"""Adds evidence to the model for a host or a connection given its network address(es) by calling the HMM's add_evidence function"""
		if dst_addr == None:
			self.hosts[(addr, port)].add_evidence()
		else:
			self.connections[((addr, port), (dst_addr, dst_port))].add_evidence()

	def update(self):
		"""Updates all hosts' and connections' HMMs using the forward algorithm and the given evidence up to this point, then updates the database"""

		# First process the newly received evidence
		self.process_evidence(self.evidence)
		
		# Apply forward algorithm
		for h in self.hosts:
			self.hosts[h].update()
		for c in self.connections:
			self.connections[c].update()
			# c is connection tuple consisting of two network address + port tuples	
			# Extract the source and destination hosts' network address tuples
			src = c[0]
			dst = c[1]
			# Raw address string of form 3.3.3.3:21 that will be used as a unique identifier in the database
			src_raw = str(c[0][0]) + ":" + str(c[0][1])
			dst_raw = str(c[1][0]) + ":" + str(c[1][1])
			# Fetch the source and destination hosts' HMMs, then src_hmm.p is the probability the source host exists given the evidence up to this point
			src_hmm = self.hosts[src]
			dst_hmm = self.hosts[dst]
			if src[0] == "8.8.8.8":
				print("p = ", src_hmm.p)
			# Now get the probability the connection exists
			conn_p = self.connections[c].p
			# Create nodes and a relationship to insert into the database
			src_node = neo.Node("Host", addr=src_raw, ip=src[0], port=src[1], p=src_hmm.p[0])
			dst_node = neo.Node("Host", addr=dst_raw, ip=dst[0] , port=dst[1], p=dst_hmm.p[0])
			connection = neo.Relationship(src_node, "CONNECTED", dst_node, p=conn_p[0])
			neo.Graph.merge(graph, connection, "Host", "addr")

	def __init__(self, subnet):
		"""Initializes the Hosts object with an empty dictionary each for hosts and connections """
		self.hosts = {}
		self.connections = {}
		self.evidence = []
		self.subnet = subnet

	def process_evidence(self, evidence):
		"""Processes the incoming evidence

		This is called on each piece of evidence that is received from clients. Here we add evidence in the model according to the data received.
		"""
		
		# Clear self.evidence
		self.evidence = []

		# Process passed evidence
		for e in evidence:
			src_addr, dst_addr = e.split("-")
			src, src_port = src_addr.split(":")
			dst, dst_port = dst_addr.split(":")
			
			self.add_host(src, src_port)
			self.add_evidence(src, src_port)
	
			# If the host is in the observed subnet, add it to the model, add the relationship to the model, and add evidence
			if ipaddress.IPv4Address(dst) in ipaddress.IPv4Network(self.subnet):
				self.add_host(dst, dst_port)
				self.add_connection(src, src_port, dst, dst_port)
				self.add_evidence(src, src_port, dst, dst_port)



class ThreadedServer(object):
	def __init__(self, host, port, hosts):
		self.host = host
		self.port = port
		self.hosts = hosts
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind((self.host, self.port))

	def listen(self):
		self.sock.listen(5)
		while True:
			client, address = self.sock.accept()
			client.settimeout(300)
			threading.Thread(target = self.listen_client, args = (client,address,self.hosts)).start()

	def remove_padding(self, data):
		data, pad = data.split("@")
		return data

	def listen_client(self, client, address, hosts):
		size = 64
		while True:
			try:
				data = client.recv(size)
				if data:
		    			# Decode the incoming data and add it to the list of evidence
					d = self.remove_padding(data.decode())
					hosts.evidence.append(d)
				else:
					raise error('disconnected')
			except:
				client.close()
				return False

port = int(input("Port: "))
subnet = input("Subnet: ")

# Establish a database connection
graph = neo.Graph(password="test")

# Make sure there are no existing nodes and relationships in the database
graph.delete_all()

# Create hosts object which will be used to keep track of hosts, add evidence and update them
hosts = Hosts(subnet)

# We will use this signal handler to update the hosts periodically (say every 5 seconds)
def handler(signum, frame):
	hosts.update()
	signal.alarm(5)

# When this signal expires the handler function updates the hosts 
signal.signal(signal.SIGALRM, handler)
signal.alarm(5)

ThreadedServer('', port, hosts).listen()
