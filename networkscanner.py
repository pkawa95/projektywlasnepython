import socket
import threading

# Funkcja sprawdzająca dostępność mostka na porcie 80
def check_ip(ip):
    try:
        socket.create_connection((ip, 80), timeout=1)
        print(f"Bridge znaleziono: {ip}")
    except socket.error:
        pass

# Funkcja skanująca zakres IP w lokalnej sieci
def scan_network(network):
    threads = []
    for i in range(1, 255):
        ip = f"{network}.{i}"
        thread = threading.Thread(target=check_ip, args=(ip,))
        threads.append(thread)
        thread.start()

    # Czekamy na zakończenie wszystkich wątków
    for thread in threads:
        thread.join()

# Wprowadź swoją sieć (np. '192.168.1')
network = "192.168.1"
scan_network(network)
