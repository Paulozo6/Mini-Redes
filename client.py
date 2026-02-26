import socket
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import os
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

class ChatCliente:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Cliente")
        
        self.ROUTTER_ADDR = ('127.0.0.1', 7000)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(2.0)  # Timeout para receber ACKs
        self.seq_num = 0
        self.usuario = None
        
        self.ack_evento = threading.Event()
        self.setup_gui()
        
    def setup_gui(self):
        self.login_frame = tk.Frame(self.master)
        self.login_frame.pack(expand=True)

        tk.Label(self.login_frame, text = "Nome de usuário:", fg = "White", bg = "#2c3e50", font = ("Arial", 12)).pack()
        self.username_entry = tk.Entry(self.login_frame, font = ("Arial", 12))
        self.username_entry.pack(pady=5)

        tk.Button(self.login_frame, text="Entrar", command=self.entrar_chat).pack(pady=10)

    def entrar_chat(self):
        self.usuario = self.username_entry.get().strip()
        if not self.usuario:
            messagebox.showerror("Erro", "Por favor, insira um nome de usuário.")
            return
        
        for porta in [6000, 6001]:
            try:
                self.client_socket.bind(('127.0.0.1', porta))
                self.minha_porta = porta
                break
            except:
                continue
        else:
            messagebox.showerror("Erro", "Todas as portas estão ocupadas. Tente novamente mais tarde.")
            return
        
        self.login_frame.pack_forget()
        self.setup_chat_gui()
        
        escuta = threading.Thread(target=self.receber_mensagens, daemon=True)
        escuta.start()
        time.sleep(0.3)  # Aguarda a thread de escuta iniciar
        
        threading.Thread(target=self.enviar_login_servidor, daemon=True).start()
    
    def receber_mensagens(self):
        while True:
            try:
                dados, _ = self.client_socket.recvfrom(4096)
                quadro_dict, integro = Quadro.deserializar(dados)
                
                if not integro or not quadro_dict:
                    continue  # Ignora quadros corrompidos ou vazios
                
                pacote = quadro_dict['data']
                segmento = pacote['data']
                vip_origem = pacote['src_vip']                
                
                if segmento.get('is_ack') and segmento.get('seq_num') == self.seq_num:
                    print('\033[92m[ACK RECEBIDO]!\033[0m')
                    self.ack_evento.set()
                    continue
                else:
                    payload = segmento.get('payload', {})
                    remetente = payload.get('sender', 'Desconecido')
                    mensagem = payload.get('message', '')
                        
                    if remetente == "SISTEMA":
                        self.exibir_mensagem(mensagem, "sistema")
                    elif remetente != self.usuario:
                        self.exibir_mensagem(f"{remetente}: {mensagem}", "outro")
            except:
                continue
    
    def setup_chat_gui(self):
        self.chat_area = scrolledtext.ScrolledText(self.master, state='disabled', width=50, height=20, font=("Arial", 12))
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.chat_area.config(bg = "#f0f2f5", fg = "#2c3e50", insertbackground = "#2c3e50")
        
        self.chat_area.tag_config("eu", foreground = "blue", font = ("Arial", 12, "bold"))
        self.chat_area.tag_config("outro", foreground = "green", font = ("Arial", 12))
        self.chat_area.tag_config("historico", foreground = "gray", font = ("Arial", 10, "italic"))
        self.chat_area.tag_config("sistema", foreground = "orange", font = ("Arial", 12, "bold"))
        
        self.message_entry = tk.Entry(self.master, font = ("Arial", 12))
        self.message_entry.pack(padx=10, pady=5, fill=tk.X)
        self.message_entry.bind("<Return>", lambda event: self.enviar_mensagem())
    
        self.send_button = tk.Button(self.master, text="Enviar", command=self.enviar_mensagem)
        self.send_button.pack(pady=5)
    
    def exibir_mensagem(self, mensagem, tipo_tag = "sistema"):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{mensagem}\n", tipo_tag)
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)
    
    def enviar_mensagem(self):
        mensagem = self.message_entry.get()
        if not mensagem:
            return
        self.message_entry.delete(0, tk.END)
    
        threading.Thread(target=self.enviar_mensagem_rede, args=(mensagem,), daemon = True).start()
    
    def enviar_mensagem_rede(self, mensagem, tipo = "chat"):
        meu_vip = "CLIENTE_1" if self.minha_porta == 6000 else "CLIENTE_2"
        dados_app = {
            "type" : tipo,
            "sender" : self.usuario,
            "message" : mensagem,
            "timestamp" : time.time()
        }   
    
        seg = Segmento(self.seq_num, is_ack = False, payload = dados_app)
        pac = Pacote(
            src_vip=meu_vip,
            dst_vip = "SERVIDOR",
            ttl = 64,
            segmento_dict = seg.to_dict()
        )
    
        qua = Quadro(src_mac = "00:11", dst_mac = "22:33", pacote_dict = pac.to_dict())
    
        bytes_enviar = qua.serializar()
        
        self.ack_evento.clear()
        
        while True:
            print(f"Enviando Seq {self.seq_num}...")
            enviar_pela_rede_ruidosa(self.client_socket, bytes_enviar, self.ROUTTER_ADDR)
        
            if self.ack_evento.wait(timeout=2.0):
                print(f"\033[92m[ENTREGUE]!\033[0m")
                if tipo != "login":
                    self.exibir_mensagem(f"{self.usuario} (Você): {mensagem}", "eu")
                self.seq_num = 1 - self.seq_num  # Alterna entre 0 e 1
                break
            else:
                print(f"\033[91m[Falha na rede] Timeout! Reenviando....\033[0m")
    
    def enviar_login_servidor(self):
        meu_vip = "CLIENTE_1" if self.minha_porta == 6000 else "CLIENTE_2"
        dados_app = {
            "type" : "login",
            "sender" : self.usuario,
            "message" : f"{self.usuario} entrou no chat",
            "timestamp" : time.time()
        }
        
        seg = Segmento(self.seq_num, is_ack = False, payload = dados_app)
        pac = Pacote(
            src_vip=meu_vip,
            dst_vip = "SERVIDOR",
            ttl = 64,
            segmento_dict = seg.to_dict()
        )
        qua = Quadro(src_mac = "00:11", dst_mac = "22:33", pacote_dict = pac.to_dict())
        
        print(f"Enviando login do usuário {self.usuario} para o servidor...")
        enviar_pela_rede_ruidosa(self.client_socket, qua.serializar(), self.ROUTTER_ADDR)

if __name__ == "__main__":
    import os
    root = tk.Tk()
    app = ChatCliente(root)
    root.mainloop()