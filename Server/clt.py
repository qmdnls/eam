import socket
import time

# Create a connection to the server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = input("Server IP address: ")
port = input("Server port: ")
port_src = input("Source port: ")
sock.bind(('',int(port_src)))
sock.connect((host,int(port)))

msg = "example"

while True:
	sock.send(msg)
	sock.recv(7)
	time.sleep(3)
