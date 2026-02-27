import socket
from protocol import Quadro, enviar_pela_rede_ruidosa

ROUTER_ADDR = ('127.0.0.1', 7000)

tabela_roteamento = {
    "SERVIDOR": ("127.0.0.1", 5000),
    "CLIENTE_1": ("127.0.0.1", 6000),
    "CLIENTE_2": ("127.0.0.1", 6001)
}

router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    router_socket.bind(ROUTER_ADDR)
    router_socket.settimeout(0.5)
    print(f"\033[93m[ROTEADOR] Iniciado em {ROUTER_ADDR}\033[0m")
except OSError as e:
    print(f"\033[91mERRO: Porta 7000 já em uso - {e}\033[0m")
    print("Rode no CMD: netstat -ano | findstr :7000")
    print("Depois: taskkill /PID <numero> /F")
    input("Pressione Enter para sair...")
    exit(1)

while True:
    try:
        dados, addr = router_socket.recvfrom(4096)
        quadro_dict, integro = Quadro.deserializar(dados)
        
        if not integro or not quadro_dict:
            print("\033[91m[ROTEADOR] Quadro corrompido\033[0m")
            continue

        pacote_data = quadro_dict['data']
        dst_vip = pacote_data['dst_vip']
        ttl = pacote_data['ttl'] - 1

        if ttl <= 0:
            print(f"\033[91m[ROTEADOR] TTL expirado: {dst_vip}\033[0m")
            continue

        if dst_vip in tabela_roteamento:
            destino = tabela_roteamento[dst_vip]
            pacote_data['ttl'] = ttl
            novo_quadro = Quadro("MAC_ROUTER", "MAC_NEXT_HOP", pacote_data)

            print(f"\033[93m[ROTEADOR] Encaminhando {pacote_data['src_vip']} → {dst_vip} | TTL={ttl}\033[0m")
            enviar_pela_rede_ruidosa(router_socket, novo_quadro.serializar(), destino)
        else:
            print(f"\033[91m[ROTEADOR] Destino desconhecido: {dst_vip}\033[0m")

    except socket.timeout:
        continue
    except Exception as e:
        print(f"\033[91m[ROTEADOR] Erro: {e}\033[0m")