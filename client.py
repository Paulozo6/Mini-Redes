import socket
import json
import time
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

ROUTER_ADDR = ('127.0.0.1', 7000)
MEU_ADDR = ('127.0.0.1', 6000)
TIMEOUT_VALUE = 2.0

def iniciar_cliente():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(MEU_ADDR)
    client.settimeout(TIMEOUT_VALUE) 

    seq_num = 0

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
        pac = Pacote(
            src_vip="CLIENTE",
            dst_vip = "SERVIDOR",
            ttl = 64,
            segmento_dict = seg.to_dict()
        )
        
        qua = Quadro(src_mac = "00:11", dst_mac = "22:33", pacote_dict = pac.to_dict())
        
        bytes_enviar = qua.serializar()
        
        ack_recebido = False
        while not ack_recebido:
            print(f"Enviando Seq {seq_num}...")
            enviar_pela_rede_ruidosa(client, bytes_enviar, ROUTER_ADDR)
            
            try:
                dados, _ = client.recvfrom(4096)
                quadro_dict, integro = Quadro.deserializar(dados)
                
                if integro:
                    segmento = quadro_dict['data']['data']
                    
                    if segmento['is_ack'] and segmento['seq_num'] == seq_num:
                        print('\033[92m[CLIENTE] ACK recebido!\033[0m')
                        ack_recebido = True
                        seq_num = 1 - seq_num
            except socket.timeout:
                print("\033[91m[CLIENTE] Timeout! Retransmitindo....\033[0m")
    print("Encerrando cliente.")
    
if __name__ == "__main__":
    iniciar_cliente()