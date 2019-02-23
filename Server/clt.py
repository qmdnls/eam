import socket
import time

# Create a connection to the server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = input("Server IP address: ")
port = input("Server port: ")
sock.connect((host,int(port)))

msg = "example message"

while True:
	sock.send(msg.encode())
	sock.recv(1024)
	time.sleep(3)
