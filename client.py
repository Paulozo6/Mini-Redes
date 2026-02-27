import socket
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
from protocol import Segmento, Pacote, Quadro, enviar_pela_rede_ruidosa

class ChatCliente:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Cliente")

        self.ROUTER_ADDR = ('127.0.0.1', 7000)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(0.5)

        self.seq_num = 0
        self.usuario = None
        self.vip = None
        self.ack_evento = threading.Event()

        self.TIMEOUT_LOGIN = 8.0
        self.MAX_TENTATIVAS_LOGIN = 12

        self.TIMEOUT_CHAT_BASE = 10.0
        self.MAX_TENTATIVAS_CHAT = 25

        self.setup_gui()

    def setup_gui(self):
        self.login_frame = tk.Frame(self.master)
        self.login_frame.pack(expand=True)
        tk.Label(self.login_frame, text="Nome de usuário:", fg="white", bg="#2c3e50", font=("Arial", 12)).pack()
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 12))
        self.username_entry.pack(pady=5)
        tk.Button(self.login_frame, text="Entrar", command=self.entrar_chat).pack(pady=10)

    def entrar_chat(self):
        self.usuario = self.username_entry.get().strip()
        if not self.usuario:
            messagebox.showerror("Erro", "Digite um nome.")
            return

        # Bind com tentativa dupla
        bind_ok = False
        for porta, vip_name in [(6000, "CLIENTE_1"), (6001, "CLIENTE_2")]:
            try:
                self.client_socket.bind(('127.0.0.1', porta))
                self.vip = vip_name
                bind_ok = True
                break
            except OSError:
                pass

        if not bind_ok:
            messagebox.showerror("Erro", "Portas 6000 e 6001 ocupadas. Feche outros clientes.")
            return

        self.login_frame.pack_forget()
        self.setup_chat_gui()

        threading.Thread(target=self.receber_mensagens, daemon=True).start()
        time.sleep(1.0)  # tempo para tudo estabilizar
        self.enviar_login()

    def setup_chat_gui(self):
        self.chat_area = scrolledtext.ScrolledText(self.master, state='disabled', width=50, height=20, font=("Arial", 12))
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_area.tag_config("eu", foreground="blue", font=("Arial", 12, "bold"))
        self.chat_area.tag_config("sistema", foreground="orange", font=("Arial", 12, "bold"))
        self.chat_area.tag_config("enviando", foreground="gray", font=("Arial", 11, "italic"))
        self.chat_area.tag_config("conectando", foreground="purple", font=("Arial", 11, "italic"))

        self.message_entry = tk.Entry(self.master, font=("Arial", 12))
        self.message_entry.pack(padx=10, pady=5, fill=tk.X)
        self.message_entry.bind("<Return>", lambda e: self.enviar_mensagem())
        tk.Button(self.master, text="Enviar", command=self.enviar_mensagem).pack(pady=5)

    def exibir_mensagem(self, texto, tag="sistema"):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{texto}\n", tag)
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def enviar_login(self):
        dados_app = {
            "type": "login",
            "sender": self.usuario,
            "message": f"{self.usuario} entrou no chat",
            "timestamp": time.time()
        }
        seg = Segmento(self.seq_num, is_ack=False, payload=dados_app)
        pac = Pacote(self.vip, "SERVIDOR", 128, seg.to_dict())
        qua = Quadro("00:11", "22:33", pac.to_dict())

        self.ack_evento.clear()
        tentativas = 0
        linha = self.chat_area.index(tk.END)
        self.exibir_mensagem("Conectando ao servidor...", "conectando")

        while tentativas < self.MAX_TENTATIVAS_LOGIN:
            self._atualizar_login(linha, tentativas + 1)
            enviar_pela_rede_ruidosa(self.client_socket, qua.serializar(), self.ROUTER_ADDR)

            if self.ack_evento.wait(timeout=self.TIMEOUT_LOGIN):
                self.seq_num = 1 - self.seq_num
                self._sucesso_login(linha)
                return

            tentativas += 1
            time.sleep(0.5)

        self._falha_login(linha)

    def _atualizar_login(self, linha, tentativa):
        texto = f"Conectando ao servidor... (tentativa {tentativa}/{self.MAX_TENTATIVAS_LOGIN})"
        self.chat_area.config(state='normal')
        self.chat_area.delete(linha, f"{linha} lineend")
        self.chat_area.insert(linha, texto + "\n", "conectando")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def _sucesso_login(self, linha):
        self.chat_area.config(state='normal')
        self.chat_area.delete(linha, f"{linha} lineend + 1 lines")
        self.chat_area.insert(linha, "Conexão estabelecida!\n", "sistema")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def _falha_login(self, linha):
        self.chat_area.config(state='normal')
        self.chat_area.delete(linha, f"{linha} lineend + 1 lines")
        self.chat_area.insert(linha, "→ Falha na conexão inicial (timeout)\n", "sistema")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def enviar_mensagem(self):
        msg = self.message_entry.get().strip()
        if not msg:
            return

        linha = self.chat_area.index(tk.END)
        self.exibir_mensagem(f"Você: {msg}  [enviando...]", "enviando")
        self.message_entry.delete(0, tk.END)

        threading.Thread(target=self._enviar_chat, args=(msg, linha), daemon=True).start()

    def _enviar_chat(self, msg, linha):
        dados_app = {"type": "chat", "sender": self.usuario, "message": msg, "timestamp": time.time()}
        seg = Segmento(self.seq_num, is_ack=False, payload=dados_app)
        pac = Pacote(self.vip, "SERVIDOR", 128, seg.to_dict())
        qua = Quadro("00:11", "22:33", pac.to_dict())

        self.ack_evento.clear()
        tentativas = 0
        timeout = self.TIMEOUT_CHAT_BASE

        while tentativas < self.MAX_TENTATIVAS_CHAT:
            self._atualizar_chat(linha, msg, tentativas + 1)
            enviar_pela_rede_ruidosa(self.client_socket, qua.serializar(), self.ROUTER_ADDR)

            if self.ack_evento.wait(timeout=timeout):
                self.seq_num = 1 - self.seq_num
                self._sucesso_chat(linha, msg)
                return

            tentativas += 1
            timeout = min(timeout * 1.3, 25.0)

        self._falha_chat(linha)

    def _atualizar_chat(self, linha, msg, tentativa):
        texto = f"Você: {msg}  [tent {tentativa}/{self.MAX_TENTATIVAS_CHAT}]"
        self.chat_area.config(state='normal')
        self.chat_area.delete(linha, f"{linha} lineend")
        self.chat_area.insert(linha, texto, "enviando")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def _sucesso_chat(self, linha, msg):
        self.chat_area.config(state='normal')
        self.chat_area.delete(linha, f"{linha} lineend + 1 lines")
        self.chat_area.insert(linha, f"Você: {msg}\n", "eu")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def _falha_chat(self, linha):
        self.chat_area.config(state='normal')
        self.chat_area.delete(linha, f"{linha} lineend + 1 lines")
        self.chat_area.insert(linha, "→ Mensagem não chegou (timeout)\n", "sistema")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def receber_mensagens(self):
        while True:
            try:
                dados, _ = self.client_socket.recvfrom(4096)
                quadro_dict, integro = Quadro.deserializar(dados)
                if not integro or not quadro_dict:
                    continue

                pacote = quadro_dict['data']
                segmento = pacote['data']
                seq_recebido = segmento.get('seq_num')

                if segmento.get('is_ack'):
                    if seq_recebido == self.seq_num:
                        self.ack_evento.set()
                    continue

                # Se o servidor enviar algo de volta (opcional)
                payload = segmento.get('payload', {})
                if payload.get('type') == 'login':
                    self.exibir_mensagem(payload.get('message'), "sistema")

            except socket.timeout:
                continue
            except Exception as e:
                print(f"[CLIENTE] Erro recv: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatCliente(root)
    root.mainloop()