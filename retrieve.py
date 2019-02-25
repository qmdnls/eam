import py2neo as neo
import xml.etree.cElementTree as ET

class Database:
	def __init__(self, password="test"):
		self.password = password

	def connect(self):
		self.graph = neo.Graph(password=self.password)

	def write(self, filename="model.xml"):
		"""Gets all nodes and relationships with p > 0.5 and writes them to an XML file which can be used to generate the final model in ArchiMate"""

		# Create XML file skeleton
		network = ET.Element("network")
		properties = ET.Element("properties")
		# Add a list of host properties that map force is going to use
		property_addr = ET.Element("property")
		property_addr_name = ET.SubElement(property_addr, "name")
		property_addr_type = ET.SubElement(property_addr, "type")
		property_addr_name.text = "address"
		property_addr_type.text = "string"

		property_ip = ET.Element("property")
		property_ip_name = ET.SubElement(property_ip, "name")
		property_ip_type = ET.SubElement(property_ip, "type")
		property_ip_name.text = "ip"
		property_ip_type.text = "string"

		property_port = ET.Element("property")
		property_port_name = ET.SubElement(property_port, "name")
		property_port_type = ET.SubElement(property_port, "type")
		property_port_name.text = "port"
		property_port_type.text = "number"

		property_likelihood = ET.Element("property")
		property_likelihood_name = ET.SubElement(property_likelihood, "name")
		property_likelihood_type = ET.SubElement(property_likelihood, "type")
		property_likelihood_name.text = "likelihood"
		property_likelihood_type.text = "number"

		# Append all properties to property node
		properties.append(property_addr)
		properties.append(property_ip)
		properties.append(property_port)
		properties.append(property_likelihood)

		# Append property node to network
		network.append(properties)

		# Get all hosts with p > 0.5 using cypher query, hosts is a list of dicts
		nodematcher = neo.NodeMatcher(self.graph)
		hosts = nodematcher.match("Host", p__gt=0.5)

		# Get all connections with p > 0.5 and both start_node.p > 0.5 and end_node.p > 0.5
		relmatcher = neo.RelationshipMatcher(self.graph)
		rels = relmatcher.match(r_type="CONNECTED").where("_.p > 0.5", "a.p > 0.5", "b.p > 0.5")

		# Iterate over all hosts and append XML nodes for each of them
		for h in hosts:
			host = ET.Element("host")
			name = ET.SubElement(host, "name")
			name.text = str(h["ip"])
			address = ET.SubElement(host, "address")
			# For the ArchiMate model does not allow colons in properties, therefore use underscores instead
			address.text = h["addr"].replace(":","_")
			property_ip = ET.SubElement(host, "property")
			property_ip_name = ET.SubElement(property_ip, "name")
			property_ip_value = ET.SubElement(property_ip, "value")
			property_ip_name.text = "ip"
			property_ip_value.text = str(h["ip"])
			property_port = ET.SubElement(host, "property")
			property_port_name = ET.SubElement(property_port, "name")
			property_port_value = ET.SubElement(property_port, "value")
			property_port_name.text = "port"
			property_port_value.text = str(h["port"])
			property_likelihood = ET.SubElement(host, "property")
			property_likelihood_name = ET.SubElement(property_likelihood, "name")
			property_likelihood_value = ET.SubElement(property_likelihood, "value")
			property_likelihood_name.text = "likelihood"
			property_likelihood_value.text = str(round(h["p"],2))
			# Append host node to network node
			network.append(host)

		# Now iterate over all "CONNECTED" relationships and add XML nodes
		for r in rels:
			rel = ET.Element("relationship")
			source = ET.SubElement(rel, "source")
			destination = ET.SubElement(rel, "destination")
			source.text = r.start_node["addr"].replace(":","_")
			destination.text = r.end_node["addr"].replace(":","_")
			property_likelihood = ET.SubElement(rel, "property")
			property_likelihood_name = ET.SubElement(property_likelihood, "name")
			property_likelihood_value = ET.SubElement(property_likelihood, "value")
			property_likelihood_name.text = "likelihood"
			property_likelihood_value.text = str(round(r["p"], 2))
			network.append(rel)		


		tree = ET.ElementTree(network)
		tree.write(filename)

db = Database(password="test")
db.connect()
db.write("file.xml")
