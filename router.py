import socket
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

ROUTER_IP = ('127.0.0.1')
ROUTER_PORT = 7000
ROUTTER_ADDR = (ROUTER_IP, ROUTER_PORT)

tabela_roteamento = {
    "SERVIDOR": ("127.0.0.1", 5000),
    "CLIENTE": ("127.0.0.1", 6000)
}

router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
router_socket.bind(ROUTTER_ADDR)

print("Roteador iniciado. Aguardando pacotes...")

while True:
    dados, addr_origem = router_socket.recvfrom(4096)
    quadro_dict, integro = Quadro.deserializar(dados)
    
    if not integro:
        print("\033[91m[ROTEADOR](ERRO DE CRC) Quadro corrompido recebido. Ignorando...")
        continue
    
    pacote_data = quadro_dict['data']
    dst_vip = pacote_data['dst_vip']
    ttl_atual = pacote_data['ttl']
    
    novo_ttl = ttl_atual - 1
    if novo_ttl <= 0:
        print(f"\033[91m[ROTEADOR] TTL expirado para destino {dst_vip}. Descartando pacote.")
        continue
    
    if dst_vip in tabela_roteamento:
        pacote_data['ttl'] = novo_ttl
        novo_quadro = Quadro(
            src_mac = "MAC_ROUTER",
            dst_mac = "MAC_DEST",
            pacote_dict =  pacote_data
        )
        print(f"\033[94m[ROTEADOR] Encaminhando pacote para {dst_vip} com TTL {novo_ttl}...")
        enviar_pela_rede_ruidosa(router_socket, novo_quadro.serializar(), tabela_roteamento[dst_vip])
    else:
        print(f"\033[91m[ROTEADOR] Destino {dst_vip} desconhecido. Descartando pacote.")