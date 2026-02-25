import socket
import json
import time
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

HOST = '127.0.0.1'
PORT = 5000
DESTINO_REAL = (HOST, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(2.0) 

seq_num = 0

print("Conectado ao servidor.")

while True:
    message = input("Digite sua mensagem: ")
    
    if message.lower() == "sair":
        break
        
    dados_app = {
        "type" : "chat",
        "sender" : "Cliente",
        "message" : message,
        "timestamp" : time.time()
    }
    
    seg = Segmento(seq_num, is_ack = False, payload = dados_app)
    pac = Pacote(src_vip="CLI", dst_vip = "SRV", ttl = 64, segmento_dict = seg.to_dict())
    qua = Quadro(src_mac = "00:11", dst_mac = "22:33", pacote_dict = pac.to_dict())
    
    bytes_enviar = qua.serializar()
    
    ack_recebido = False
    while not ack_recebido:
        print(f"Enviando Seq {seq_num}...")
        enviar_pela_rede_ruidosa(client, bytes_enviar, DESTINO_REAL)
        
        try:
            dados, _ = client.recvfrom(4096)
            quadro_dict, integro = Quadro.deserializar(dados)
            
            if integro:
                segmento = quadro_dict['data']['data']
                
                if segmento['is_ack'] and segmento['seq_num'] == seq_num:
                    print('ACK recebido!')
                    ack_recebido = True
                    seq_num = 1 - seq_num
        except socket.timeout:
            print("Timeout! Retransmitindo....")