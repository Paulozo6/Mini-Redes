import subprocess
import time
import sys
import os

def iniciar():
    print("----- Iniciando Simulação Mini-NET (apenas 1 Cliente) -----")
    
    processos = []
    
    # Roteador
    print("[SISTEMA] Iniciando roteador...")
    p_router = subprocess.Popen('start cmd /k "title ROTEADOR & python router.py"', shell=True)
    processos.append(p_router.pid)
    time.sleep(3.0)
    
    # Servidor
    print("[SISTEMA] Iniciando servidor...")
    p_server = subprocess.Popen('start cmd /k "title SERVIDOR & python server.py"', shell=True)
    processos.append(p_server.pid)
    time.sleep(2.0)
    
    # Cliente único
    print("[SISTEMA] Iniciando cliente...")
    p_client = subprocess.Popen('start cmd /k "title CLIENTE & python client.py"', shell=True)
    processos.append(p_client.pid)
    
    print("----------------------------------------")
    print("Simulação iniciada. Para parar: Ctrl+C aqui ou feche as janelas.")
    print("PIDs:", processos)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SISTEMA] Encerrando...")
        for pid in processos:
            try:
                os.system(f"taskkill /PID {pid} /F >nul 2>&1")
            except:
                pass
        sys.exit(0)

if __name__ == "__main__":
    iniciar()