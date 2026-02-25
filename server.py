import socket
from datetime import datetime
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

ROUTER_ADDR = ('127.0.0.1', 7000)
MEU_ADDR_REAL= ('127.0.0.1', 5000)

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(MEU_ADDR_REAL)

print("Servidor ligando. Aguardando mensagens via roteador...")

ultimo_seq_recebido = -1

while True:
    dados_brutos, _ = server.recvfrom(4096)
    quadro_dict, integro = Quadro.deserializar(dados_brutos)
    
    if not integro: 
        print("\033[91m[ERRO DE CRC] Quadro corrompido recebido. Ignorando...\033[0m")
        continue
    
    pacote_dict = quadro_dict['data']
    segmento_dict = pacote_dict['data']
    seq_recebida = segmento_dict['seq_num']
    
    print(f"Recebido Seq {seq_recebida}. Enviando ACK...")

    ack_seg = Segmento(seq_recebida, is_ack = True, payload = None)
    ack_pac = Pacote(src_vip = "SERVIDOR", dst_vip = "CLIENTE", ttl = 64, segmento_dict = ack_seg.to_dict())
    ack_qua = Quadro(src_mac = "MAC_SVR", dst_mac = "MAC_ROUTER", pacote_dict = ack_pac.to_dict())
    
    print(f"\033[92m[SERVIDOR] Seq {seq_recebida} recebida. Enviando ACK.\033[0m")
    
    bytes_enviar = ack_qua.serializar()
    enviar_pela_rede_ruidosa(server, bytes_enviar, ROUTER_ADDR)
    
    if seq_recebida != ultimo_seq_recebido:
        payload = segmento_dict['payload']
        print("Nova mensagem recebida:")
        hora = datetime.now().strftime('%H:%M:%S')
        print(f"\033[94m[{payload['sender']} - {hora}] {payload['message']}\033[0m")
        ultimo_seq_recebido = seq_recebida
    else:
        print("[SERVIDOR] Mensagem duplicada recebida. Ignorando conteúdo.")