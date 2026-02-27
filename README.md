 Mini-NET – Simulação de Rede com Chat Confiável (UDP)

Este projeto implementa uma simulação didática de uma rede em camadas, com:

- Cliente com interface gráfica (Tkinter)
- Servidor de aplicação (chat)
- Roteador simulando encaminhamento IP
- Enlace com ruído (perda e corrupção de pacotes)
- Protocolo de transporte confiável sobre UDP (ACK + retransmissão)

## 📡 Arquitetura

CLIENTE → ROTEADOR → SERVIDOR  
SERVIDOR → ROTEADOR → CLIENTE  

Cada camada é simulada:
- **Aplicação**: chat (login e mensagens)
- **Transporte**: Stop-and-Wait (ACK, retransmissão, controle de duplicatas)
- **Rede**: VIP, TTL e roteamento
- **Enlace**: quadros com CRC
- **Físico**: rede ruidosa simulada

## ▶️ Como executar

```bash
python main.py