import subprocess
import time
import sys


def iniciar():
    print("-----Iniciando Simulação Mini-NET-----")
    
    print("[SISTEMA] Iniciando roteador em nova janela...")
    subprocess.Popen("start cmd /k \"title Roteador & python router.py\"", shell=True)
    time.sleep(1)  # Aguarda o roteador iniciar
    
    print("[SISTEMA] Iniciando servidor...")
    subprocess.Popen("start cmd /k \"title Servidor & python server.py\"", shell=True)
    time.sleep(1)  # Aguarda o servidor iniciar
    
    print("[SISTEMA] Iniciando cliente...")
    print("----------------------------------------")
    try:
        subprocess.run([sys.executable, "client.py"])
    except KeyboardInterrupt:
        print("\n[SISTEMA] Encerrando simulação...")
        sys.exit(0)
if __name__ == "__main__":
    iniciar()
    