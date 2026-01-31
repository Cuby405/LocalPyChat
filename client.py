import os
import socket
import threading
import hashlib
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import time

APP_VERSION = "1.0.0"

# =====================
# CONFIGURACIÓN
# =====================
BASE_DIR = os.path.join(os.path.dirname(__file__), ".data")
os.makedirs(BASE_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(BASE_DIR, "config.txt")
PORT = 23456

def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

# =====================
# TK INIT
# =====================
root = tk.Tk()
root.withdraw()

# =====================
# CARGAR CONFIG
# =====================
config = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v

# =====================
# LOGIN (SIEMPRE)
# =====================
USER = simpledialog.askstring("Usuario", "Nombre de usuario:")
if not USER:
    exit()

pwd = simpledialog.askstring("Contraseña", "Contraseña:", show="*")
if not pwd:
    exit()
PWD_HASH = hash_pwd(pwd)

if "color" not in config:
    config["color"] = simpledialog.askstring("Color", "Color HEX (#ffffff):") or "#ffffff"

if "ip" not in config:
    config["ip"] = simpledialog.askstring("Servidor", "IP del servidor:")
    if not config["ip"]:
        exit()

COLOR = config["color"]
SERVER_IP = config["ip"]

# Guardar configuración
with open(CONFIG_FILE, "w") as f:
    f.write(f"user={USER}\n")
    f.write(f"pwd_hash={PWD_HASH}\n")
    f.write(f"color={COLOR}\n")
    f.write(f"ip={SERVER_IP}\n")

import urllib.request

IGNORED_VERSION_FILE = os.path.join(BASE_DIR, "ignored_version.txt")

def get_ignored_version():
    if os.path.exists(IGNORED_VERSION_FILE):
        return open(IGNORED_VERSION_FILE).read().strip()
    return None


def check_update():
    try:
        url = "https://raw.githubusercontent.com/Cuby405/LocalPyChat/main/version.txt"
        with urllib.request.urlopen(url, timeout=3) as r:
            online_version = r.read().decode().strip()

        ignored = get_ignored_version()

        if online_version != APP_VERSION and online_version != ignored:
            return online_version
    except:
        pass
    return None

# =====================
# SOCKET
# =====================
sock = None
user_colors = {}

def connect_to_server():
    global sock
    while True:
        try:
            sock = socket.socket()
            sock.settimeout(5)
            sock.connect((SERVER_IP, PORT))
            login_msg = f"__LOGIN__:{USER}|{PWD_HASH}|{COLOR}"
            sock.send(login_msg.encode())

            response = sock.recv(1024).decode()
            if response == "__DENY__":
                messagebox.showerror("Error", "Usuario inválido o contraseña incorrecta")
                sock.close()
                root.destroy()
                return
            break
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar:\n{e}")
            time.sleep(5)

def receive_messages():
    while True:
        try:
            msg = sock.recv(1024).decode()
            msgs = msg.split("\n")

            for single_msg in msgs:
                if not single_msg.strip():
                    continue

                # ===== MENSAJE DE SISTEMA (USUARIOS) =====
                if single_msg.startswith("__USERS__"):
                    users_raw = single_msg.split(":", 1)[1]
                    users_list = users_raw.split(",")

                    user_colors.clear()
                    for u in users_list:
                        if "|" in u:
                            name, color = u.split("|", 1)
                            user_colors[name] = color

                    if USER not in user_colors:
                        user_colors[USER] = COLOR

                    users_area.configure(state='normal')
                    users_area.delete(1.0, tk.END)
                    for u, c in user_colors.items():
                        users_area.insert(tk.END, u + "\n", u)
                        users_area.tag_config(u, foreground=c)
                    users_area.configure(state='disabled')

                    continue  # 🔴 CLAVE: NO PASA AL CHAT

                # ===== MENSAJE NORMAL DE CHAT =====
                chat_area.configure(state='normal')
                if ":" in single_msg:
                    user_name, message = single_msg.split(":", 1)
                    color = user_colors.get(user_name, "#ffffff")
                    chat_area.insert(tk.END, f"{user_name}: ", user_name)
                    chat_area.tag_config(user_name, foreground=color)
                    chat_area.insert(tk.END, message.strip() + "\n", "text")
                else:
                    chat_area.insert(tk.END, single_msg + "\n", "text")
                chat_area.configure(state='disabled')
                chat_area.see(tk.END)

        except:
            time.sleep(1)

def send_message(event=None):
    msg = message_entry.get().strip()
    if not msg:
        return
    try:
        sock.send(f"{USER}:{msg}".encode())
        message_entry.delete(0, tk.END)
    except:
        messagebox.showerror("Error", "No conectado")

def clear_chat():
    chat_area.configure(state='normal')
    chat_area.delete(1.0, tk.END)
    chat_area.configure(state='disabled')

def change_ip():
    global SERVER_IP, sock

    try:
        if sock:
            sock.close()
    except:
        pass

    new_ip = simpledialog.askstring(
        "Cambiar servidor",
        "Nueva IP del servidor:"
    )

    if not new_ip:
        return  # cancelar = no hacer nada

    SERVER_IP = new_ip
    config["ip"] = new_ip

    # guardar SOLO la IP nueva
    with open(CONFIG_FILE, "w") as f:
        f.write(f"user={USER}\n")
        f.write(f"pwd_hash={PWD_HASH}\n")
        f.write(f"color={COLOR}\n")
        f.write(f"ip={SERVER_IP}\n")

    clear_chat()

    threading.Thread(target=connect_to_server, daemon=True).start()

# =====================
# UI
# =====================
root.deiconify()
root.title(f"Chat - {USER}")
root.geometry("800x500")
root.configure(bg="black")

main_frame = tk.Frame(root, bg="black")
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

chat_area = scrolledtext.ScrolledText(
    main_frame, bg="black", fg="white",
    insertbackground="white", state="disabled"
)
chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
chat_area.tag_config("text", foreground="white")

users_area = scrolledtext.ScrolledText(
    main_frame, width=20, bg="black", fg="white", state="disabled"
)
users_area.pack(side=tk.RIGHT, fill=tk.Y)

message_frame = tk.Frame(root, bg="black")
message_frame.pack(fill=tk.X, padx=10, pady=5)

message_entry = tk.Entry(
    message_frame, bg="#222222", fg="white", insertbackground="white"
)
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
message_entry.bind("<Return>", send_message)

send_button = tk.Button(
    message_frame, text="Enviar",
    command=send_message, bg="#333333", fg="white"
)
send_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(
    message_frame, text="Limpiar",
    command=clear_chat, bg="#444444", fg="white"
)
clear_button.pack(side=tk.LEFT, padx=5)

exit_button = tk.Button(
    message_frame, text="Cambiar IP",
    command=change_ip, bg="#550000", fg="white"
)
exit_button.pack(side=tk.LEFT, padx=5)

new_version = check_update()
if new_version:
    if messagebox.askyesno(
        "Actualización disponible",
        f"Nueva versión: {new_version}\n\n"
        "¿Quieres actualizar ahora?"
    ):
        import subprocess, sys
        subprocess.Popen([
            sys.executable,
            "updater.py",
            new_version
        ])
        root.destroy()
        exit()
    else:
        with open(IGNORED_VERSION_FILE, "w") as f:
            f.write(new_version)

# =====================
# THREADS
# =====================
threading.Thread(target=connect_to_server, daemon=True).start()
threading.Thread(target=receive_messages, daemon=True).start()

root.mainloop()
