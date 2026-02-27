import socket
import os
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    server.bind(('127.0.0.1', 5000))
    server.settimeout(0.5)
except OSError as e:
    print(f"\033[91mERRO: Porta 5000 em uso - {e}\033[0m")
    input("Pressione Enter para sair...")
    exit(1)

ultimo_seq = {}

os.system('cls' if os.name == 'nt' else 'clear')
print("\033[96m[SERVIDOR] Online\033[0m")

while True:
    try:
        dados, addr = server.recvfrom(4096)
        quadro, integro = Quadro.deserializar(dados)
        
        if not integro:
            print("\033[91m[SERVER] CRC inválido\033[0m")
            continue

        pacote = quadro['data']
        segmento = pacote['data']
        src_vip = pacote['src_vip']
        seq = segmento.get('seq_num')

        # ACK imediato
        ack_seg = Segmento(seq, is_ack=True, payload=None)
        ack_pac = Pacote("SERVIDOR", src_vip, 128, ack_seg.to_dict())
        ack_qua = Quadro("MAC_SVR", "MAC_ROUTER", ack_pac.to_dict())
        enviar_pela_rede_ruidosa(server, ack_qua.serializar(), ('127.0.0.1', 7000))
        print(f"\033[92m[SERVER] ACK enviado para {src_vip} (seq={seq})\033[0m")

        if ultimo_seq.get(src_vip) == seq:
            print(f"[SERVER] Duplicata ignorada")
            continue
        ultimo_seq[src_vip] = seq

        payload = segmento['payload']
        sender = payload.get('sender', 'Desconhecido')
        msg = payload.get('message', '')
        tipo = payload.get('type', 'chat')

        if tipo == 'login':
            print(f"\033[94m[APP] {sender} entrou no chat ({src_vip})\033[0m")
        else:
            print(f"\033[94m[APP] {sender}: {msg} ({src_vip})\033[0m")

        # Eco para o remetente (mostra a mensagem no próprio cliente)
        eco_seg = Segmento(seq, is_ack=False, payload=payload)
        eco_pac = Pacote("SERVIDOR", src_vip, 128, eco_seg.to_dict())
        eco_qua = Quadro("MAC_SVR", "MAC_ROUTER", eco_pac.to_dict())
        enviar_pela_rede_ruidosa(server, eco_qua.serializar(), ('127.0.0.1', 7000))
        print(f"[SERVER] Eco enviado para {src_vip}")

    except socket.timeout:
        continue
    except Exception as e:
        print(f"\033[91m[SERVER] Erro: {e}\033[0m")