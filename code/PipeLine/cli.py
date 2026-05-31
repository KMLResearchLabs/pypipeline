import shutil
import sys
import fcntl
import shlex
import socket
import struct
import statistics
import subprocess
import platform
import re
from ping3 import ping
import time
from pathlib import Path
from werkzeug.datastructures import FileStorage
import logging
from threading import Thread
from werkzeug.serving import make_server
from app import app
from core import (
    list_files,
    save_and_compress,
    UPLOAD_FOLDER,
)

server_thread = None
http_server = None
SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 5000


def testar_internet():
    HOST = "1.1.1.1"
    PINGS = 20


    def ping_once(host):
        parametro = "-n" if platform.system().lower() == "windows" else "-c"

        resultado = subprocess.run(
            ["ping", parametro, "1", host],
            capture_output=True,
            text=True
        )

        if resultado.returncode != 0:
            return None

        match = re.search(
            r"(?:time|tempo)[=<]?\s*(\d+(?:[.,]\d+)?)",
            resultado.stdout,
            re.IGNORECASE
        )

        if match:
            return float(match.group(1).replace(",", "."))

        return None


    def testar_rede():
        print(f"\n [*] Testing {HOST} ({PINGS} packets)\n")

        latencias = []

        for i in range(PINGS):
            latencia = ping_once(HOST)

            if latencia is not None:
                latencias.append(latencia)
                print(f"[{i+1:02d}] {latencia:.2f} ms")
            else:
                print(f"[{i+1:02d}] timeout")

            time.sleep(0.2)

        print("\n" + "=" * 40)

        recebidos = len(latencias)
        perdidos = PINGS - recebidos

        perda_pct = (perdidos / PINGS) * 100

        if recebidos == 0:
            print(" [ERROR] No responses received.")
            return

        media = statistics.mean(latencias)
        minimo = min(latencias)
        maximo = max(latencias)

        jitter = 0
        if len(latencias) > 1:
            diferencas = [
                abs(latencias[i] - latencias[i - 1])
                for i in range(1, len(latencias))
            ]
            jitter = statistics.mean(diferencas)

        print(" NETWORK REPORT")
        print(" -" * 40)
        print(f" Packets sent     : {PINGS}")
        print(f" Packets received : {recebidos}")
        print(f" Packet loss      : {perda_pct:.2f}%")
        print(f" Average ping     : {media:.2f} ms")
        print(f" Minimum ping     : {minimo:.2f} ms")
        print(f" Maximum ping     : {maximo:.2f} ms")
        print(f" Jitter           : {jitter:.2f} ms")
        print(" -" * 40)

        print("ASSESSMENT")

        if perda_pct > 5:
            print(" [!!!] High packet loss")
        elif media > 100:
            print(" [!!] High latency")
        elif jitter > 30:
            print(" [!] Unstable connection")
        else:
            print(" [OK] Suitable for hosting a local server")

    testar_rede()


def testar_pings():
    hosts = [
        "192.168.0.1",
        "8.8.8.8",
        "1.1.1.1",
        "9.9.9.9",
        "149.112.112.112",
        "208.67.222.222",
        "208.67.220.220",
        "64.6.64.6",
        "64.6.65.6",
        "76.76.19.19",
        "76.223.122.150",
        "94.140.14.14",
        "94.140.15.15",
        "185.228.168.9",
        "185.228.169.9",
        "77.88.8.8",
        "77.88.8.1",
        "8.26.56.26",
        "8.20.247.20",
        "156.154.70.1",
        "156.154.71.1",
        "198.101.242.72",
        "45.90.28.0",
        "45.90.30.0",
        "google.com",
        "cloudflare.com",
        "microsoft.com",
        "github.com",
        "wikipedia.org",
        "mozilla.org",
        "ubuntu.com",
        "python.org",
        "kernel.org",
        "duckduckgo.com",
        "openstreetmap.org",
        "archive.org",
        "ietf.org",
        "icann.org",
        "example.com",
    ]

    parametro = "-n" if platform.system().lower() == "windows" else "-c"

    sucessos = 0
    falhas = 0

    print("\n[*] Running ping protocol test...\n")

    print(f"{'STATUS':<10} {'HOST':<22} {'CODE':<6} {'LATENCY'}")
    print("-" * 55)

    for host in hosts:
        try:
            resultado = subprocess.run(
                ["ping", parametro, "1", host],
                capture_output=True,
                text=True,
                timeout=5
            )

            if resultado.returncode == 0:
                saida = resultado.stdout

                match = re.search(
                    r"(?:time|tempo)[=<]?\s*(\d+(?:[.,]\d+)?)",
                    saida,
                    re.IGNORECASE
                )

                if match:
                    latencia = float(match.group(1).replace(",", "."))
                    print(
                        f"{'OK':<10} "
                        f"{host:<22} "
                        f"{resultado.returncode:<6} "
                        f"{latencia:>7.2f} ms"
                    )
                else:
                    print(
                        f"{'OK':<10} "
                        f"{host:<22} "
                        f"{resultado.returncode:<6} "
                        f"{'N/A':>7}"
                    )

                sucessos += 1

            else:
                print(
                    f"{'ERROR':<10} "
                    f"{host:<22} "
                    f"{resultado.returncode:<6} "
                    f"{'FAILED':>7}"
                )

                falhas += 1

        except subprocess.TimeoutExpired:
            print(
                f"{'TIMEOUT':<10} "
                f"{host:<22} "
                f"{'-':<6} "
                f"{'5.0s':>7}"
            )

            falhas += 1

        except Exception as e:
            print(
                f"{'ERROR':<10} "
                f"{host:<22} "
                f"{'-':<6} "
                f"{str(e)[:20]}"
            )

            falhas += 1

    print("-" * 55)
    print(f"Hosts testados : {len(hosts)}")
    print(f"Sucessos       : {sucessos}")
    print(f"Falhas         : {falhas}")



def get_default_interface():
    try:
        with open("/proc/net/route", "r") as route_file:
            next(route_file)
            for line in route_file:
                fields = line.split()
                if len(fields) >= 2 and fields[1] == "00000000":
                    return fields[0]
    except OSError:
        return None

    return None


def get_interface_ip(interface_name):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            packed_name = struct.pack("256s", interface_name[:15].encode())
            address = fcntl.ioctl(sock.fileno(), 0x8915, packed_name)[20:24]
            return socket.inet_ntoa(address)
    except OSError:
        return None


def get_local_ips():
    ips = []
    default_interface = get_default_interface()
    if default_interface:
        default_ip = get_interface_ip(default_interface)
        if default_ip and not default_ip.startswith("127."):
            return [default_ip]

    for _, interface_name in socket.if_nameindex():
        ip = get_interface_ip(interface_name)

        if ip and not ip.startswith(("10.", "127.")) and ip not in ips:
            ips.append(ip)

    return ips


def find_available_port(start_port, attempts=20):
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((SERVER_HOST, port))
            except OSError:
                continue

        return port

    return None


def run_server():
    http_server.serve_forever()


def cmd_serve():
    global http_server, server_thread

    print("\r [*] Iniciando servidor...", end="")

    time.sleep(2)

    if server_thread and server_thread.is_alive():
        print("\r [ OK ] Servidor iniciado com sucesso.", end="")
        time.sleep(2)
        return

    logging.getLogger("werkzeug").disabled = True
    app.logger.disabled = True

    port = find_available_port(DEFAULT_SERVER_PORT)
    if port is None:
        print("\r [ERROR] Nenhuma porta livre entre 5000 e 5019.", end="")
        time.sleep(2)
        return

    http_server = make_server(SERVER_HOST, port, app)

    server_thread = Thread(
        target=run_server,
        daemon=True
    )

    server_thread.start()

    if port != DEFAULT_SERVER_PORT:
        print(f"[INFO] Porta {DEFAULT_SERVER_PORT} ocupada; usando {port}.")
        time.sleep(2)

    print(f"\r [ OK ] Servidor iniciado em http://127.0.0.1:{port}")
    time.sleep(2)
    local_ips = get_local_ips()
    if not local_ips:
        print(" [ERROR] Nenhum IP de rede local para abrir a rede.")
        print(" [INFO] Veja o IP do computador com: ip addr")
        time.sleep(2)
        return

    print(" [ OK ] Para acessar a rede, tente:")
    time.sleep(2)
    for ip in local_ips:
        print(f"    [+] http://{ip}:{port}")
        time.sleep(0.5)


def cmd_list():
    files = list_files()

    if not files:
        print(" [ERROR] Nenhum arquivo encontrado.")
        return

    print("="*30)

    for f in files:
        print(f" [+] {f['display']} -> {f['storage']}")

    print("="*30)


def cmd_upload(path):
    path = Path(path)

    if not path.exists():
        print(" [ERROR] Arquivo não encontrado.")
        return

    with open(path, "rb") as f:
        file = FileStorage(
            stream=f,
            filename=path.name
        )

        result = save_and_compress(file)

    print(f" [ OK ] enviado: {result}")


def cmd_download(filename):
    src = UPLOAD_FOLDER / filename

    if not src.exists():
        print(" [ERROR] Arquivo não encontrado.")
        return

    dst = Path.cwd() / filename

    shutil.copy(src, dst)

    print(f" [ OK ] baixado: {dst}")


def cmd_help():
    print("""
Comandos disponíveis:

 list
    Lista os arquivos armazenados

 upload <arquivo>
    Comprime e envia um arquivo

 download <arquivo>
    Baixa um arquivo para a pasta atual

 start
    Inicia o servidor web local

 ping
    Testa o ping para uma lista de hosts públicos e privados
          
 test
    Testa a qualidade da conexão com a internet

 clear
    Limpa a tela

 help
    Mostra esta ajuda

 exit
    Fecha o programa
""")


def banner():
    print("""
 ██████╗ ██╗   ██╗██████╗ ██╗██████╗ ███████╗██╗     ██╗███╗   ██╗███████╗
 ██╔══██╗╚██╗ ██╔╝██╔══██╗██║██╔══██╗██╔════╝██║     ██║████╗  ██║██╔════╝
 ██████╔╝ ╚████╔╝ ██████╔╝██║██████╔╝█████╗  ██║     ██║██╔██╗ ██║█████╗  
 ██╔═══╝   ╚██╔╝  ██╔═══╝ ██║██╔═══╝ ██╔══╝  ██║     ██║██║╚██╗██║██╔══╝  
 ██║        ██║   ██║     ██║██║     ███████╗███████╗██║██║ ╚████║███████╗
 ╚═╝        ╚═╝   ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝
                                                                         
 PyPipeLine Local Drive - CLI
 Por ByKurebo (Kauan M.) - 2026
 Digite 'help' para ajuda.\n         
""")


def clear_screen():
    print("\033c", end="")
    banner()


def parse_single_arg(arg_text):
    if not arg_text:
        return None

    try:
        parts = shlex.split(arg_text)
    except ValueError:
        return arg_text

    if len(parts) == 1:
        return parts[0]

    return arg_text


def shell():

    banner()

    while True:

        try:

            command_line = input("\n [PPL @ LocalDrive]\n" + r" \-> ").strip()

            if not command_line:
                continue

            parts = command_line.split(maxsplit=1)
            cmd = parts[0]
            arg_text = parts[1] if len(parts) == 2 else ""

            if cmd == "list":
                cmd_list()

            elif cmd == "upload":

                path = parse_single_arg(arg_text)
                if path is None:
                    print(" Uso: upload <arquivo>")
                    continue

                cmd_upload(path)

            elif cmd == "download":

                filename = parse_single_arg(arg_text)
                if filename is None:
                    print(" Uso: download <arquivo>")
                    continue

                cmd_download(filename)

            elif cmd == "start":
                cmd_serve()

            elif cmd == "ping":
                testar_pings()
            
            elif cmd == "test":
                testar_internet()

            elif cmd == "clear":
                clear_screen()

            elif cmd == "help":
                cmd_help()

            elif cmd == "exit":
                print(" [ OK ] Encerrando...")
                sys.exit(0)

            else:
                print(f" [ERROR] Comando desconhecido: {cmd}")

        except KeyboardInterrupt:
            print("\n [ERROR] Use 'exit' para sair.")

        except EOFError:
            print("\n [ OK ] Encerrando...")
            sys.exit(0)

        except Exception as e:
            print(f" [ERROR] Erro: {e}")


if __name__ == "__main__":
    shell()
