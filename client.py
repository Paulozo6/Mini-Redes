import socket
import json
import time

HOST = '127.0.0.1'
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))  

print("Conectado ao servidor.")

while True:
    message = input("Digite sua mensagem: ")
    
    if message.lower() == "sair":
        break
    
    pacote = {
        "type" : "chat",
        "sender" : "Cliente",
        "message" : message,
        "timestamp" : time.time()
    }
    
    client.send(json.dumps(pacote).encode())