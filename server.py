import socket
import json
from datetime import datetime
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

HOST = '127.0.0.1'
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print("Servidor ligano. Aguardando mensagens...")

ultimo_seq_recebido = 1

while True:
    dados_brutos, addr_cliente = server.recvfrom(4096)
    quadro_dict, integro = Quadro.deserializar(dados_brutos)
    
    if not integro: 
        print("(ERRO DE CRC) Quadro corrompido recebido. Ignorando...")
        continue
    
    pacote_dict = quadro_dict['data']
    segmento_dict = pacote_dict['data']
    payload = segmento_dict['payload']
    seq_num = segmento_dict['seq_num']
    
    print(f"Recebido Seq {seq_num}. Enviando ACK...")

    ack_seg = Segmento(seq_num, is_ack = True, payload = None)
    ack_pac = Pacote(src_vip = "SERVIDOR", dst_vip = "CLIENTE", ttl = 64, segmento_dict = ack_seg.to_dict())
    ack_qua = Quadro(src_mac = "22:33", dst_mac = "00:11", pacote_dict = ack_pac.to_dict())
    
    bytes_enviar = ack_qua.serializar()
    enviar_pela_rede_ruidosa(server, bytes_enviar, addr_cliente)
    
    if seq_num != ultimo_seq_recebido:
        print("Nova mensagem recebida:")
        hora = datetime.now().strftime('%H:%M:%S')
        print(f"[{payload['sender']} - {hora}] {payload['message']}")
        ultimo_seq_recebido = seq_num
    else:
        print("Mensagem duplicada recebida. Ignorando conteúdo.")