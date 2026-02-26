import socket
from datetime import datetime
import os
import time
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

ROUTER_ADDR = ('127.0.0.1', 7000)
MEU_ADDR_REAL= ('127.0.0.1', 5000)

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(MEU_ADDR_REAL)

usuarios_conectados = {}
ultimo_seq_recebido = {}
        
os.system('cls' if os.name == 'nt' else 'clear')
print("\033[96m" + "=" *50)
print("   Simulação de Chat - Servidor]")
print("=" *50 + "\033[0m")

while True:
    dados_brutos, addr_origem = server.recvfrom(4096)
    quadro_dict, integro = Quadro.deserializar(dados_brutos)
    
    if not integro: 
        print("\033[91m[ERRO DE CRC] Quadro corrompido recebido. Ignorando...\033[0m")
        continue
    
    pacote_dict = quadro_dict['data']
    segmento_dict = pacote_dict['data']
    payload = segmento_dict['payload']
    vip_origem = pacote_dict['src_vip']
    seq_recebida = segmento_dict['seq_num']
    nome_usuario = payload['sender']
    
    usuarios_conectados[nome_usuario] = vip_origem
    
    print(f"Recebido Seq {seq_recebida}. Enviando ACK...")

    ack_seg = Segmento(seq_recebida, is_ack = True, payload = None)
    ack_pac = Pacote("SERVIDOR", vip_origem, 64, ack_seg.to_dict())
    ack_qua = Quadro("MAC_SVR", "MAC_ROUTER", ack_pac.to_dict())
    print(f"\033[92m[SERVIDOR] Seq {seq_recebida} de {nome_usuario} recebida. Enviando ACK.\033[0m")
    enviar_pela_rede_ruidosa(server, ack_qua.serializar(), ROUTER_ADDR)
    
    if ultimo_seq_recebido.get(nome_usuario) == seq_recebida:
        print(f"[SERVIDOR] Mensagem duplicada recebida {nome_usuario}. Ignorando conteúdo.")
        continue
    
    ultimo_seq_recebido[nome_usuario] = seq_recebida
    
    print(f"\033[94m[SERVIDOR] Usuario: {payload['sender']}\033[0m")
    if payload.get('type') == 'login':
        print(f"\033[92m[LOGIN] {nome_usuario} conectado.\033[0m")
        
    elif payload['type'] == 'chat':
        print(f"\033[92m[MSG] {payload['sender']}: {payload['message']}\033[0m")
        
        for nome, vip_dest in usuarios_conectados.items():
            if nome != nome_usuario:
                print(f"\033[93m[SERVIDOR] Enviando mensagem de {nome_usuario} para {nome} ({vip_dest})...\033[0m")
                
                dados_repasse = {
                    "type" : "chat",
                    "sender" : nome_usuario,
                    "message" : payload['message'],
                    "timestamp" : time.time()
                }
                
                seg_repasse = Segmento(0, False, dados_repasse)
                pac_repasse = Pacote("SERVIDOR", vip_dest, 64, seg_repasse.to_dict())
                qua_repasse = Quadro("MAC_SVR", "MAC_ROUTER", pac_repasse.to_dict())
                
                enviar_pela_rede_ruidosa(server, qua_repasse.serializar(), ROUTER_ADDR)