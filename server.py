import socket
import threading

HOST = "0.0.0.0"
PORT = 23456

clients = {}
messages_history = []
users_db = {}
lock = threading.Lock()

def broadcast(msg):
    for c in list(clients.keys()):
        try:
            c.send((msg + "\n").encode())
        except:
            pass

def send_users():
    users = ",".join([f"{u}|{c}" for u, c in clients.values()])
    broadcast(f"__USERS__:{users}")

def handle_client(sock):
    try:
        # ===== LOGIN =====
        data = sock.recv(1024).decode()
        if not data.startswith("__LOGIN__"):
            sock.close()
            return

        _, payload = data.split(":", 1)
        user, pwd_hash, color = payload.split("|")

        with lock:
            if user in users_db and users_db[user] != pwd_hash:
                sock.send("__DENY__".encode())
                sock.close()
                return

            users_db[user] = pwd_hash
            clients[sock] = (user, color)

            # enviar historial SOLO UNA VEZ
            for old_msg in messages_history:
                sock.send((old_msg + "\n").encode())

            send_users()

        # ===== MENSAJES =====
        while True:
            msg = sock.recv(1024).decode()
            if not msg:
                break

            with lock:
                messages_history.append(msg)
                broadcast(msg)

    except:
        pass

    finally:
        with lock:
            if sock in clients:
                del clients[sock]
                send_users()
        sock.close()

server = socket.socket()
server.bind((HOST, PORT))
server.listen()

print(f"Servidor escuchando en {HOST}:{PORT}")

while True:
    s, _ = server.accept()
    threading.Thread(
        target=handle_client,
        args=(s,),
        daemon=True
    ).start()