import socket
import threading

class ThreadedServer(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind((self.host, self.port))

	def listen(self):
		self.sock.listen(5)
		while True:
			client, address = self.sock.accept()
			client.settimeout(300)
			threading.Thread(target = self.listen_client, args = (client,address)).start()

	def listen_client(self, client, address):
		size = 7
		while True:
			try:
				data = client.recv(size)
				if data:
					client.send(data)
				else:
					raise error('disconnected')
			except:
				client.close()
				return False

port = int(input("Port: "))
ThreadedServer('', port).listen()
