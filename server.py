import socket
import json
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Servidor ligando...")
conn, adr = server.accept()
print("Cliente conectado:", adr)

while True:
    data = conn.recv(1024)
    if not data:
        break
    
    mensagem = json.loads(data.decode())
    
    hora = datetime.fromtimestamp(mensagem['timestamp']).strftime('%H:%M:%S')
    print(f"[{mensagem['sender']} - {hora}] {mensagem['message']}")