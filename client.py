import os
import socket
import threading
import hashlib
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox, colorchooser
import time
import sys
import webbrowser
import urllib.request
import subprocess
import json

APP_VERSION = "1.0.0"
PORT = 23456

# =====================
# PATHS
# =====================
BASE_DIR = os.path.join(os.path.dirname(__file__), ".data")
os.makedirs(BASE_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(BASE_DIR, "config.txt")
IGNORED_VERSION_FILE = os.path.join(BASE_DIR, "ignored_version.txt")
CHATS_FILE = os.path.join(BASE_DIR, "chats.json")

# =====================
# HELPERS
# =====================
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =====================
# BUG REPORT
# =====================
def open_bug_report():
    webbrowser.open("https://forms.gle/J1rGNk6vx5iy7wdV9")

# =====================
# UPDATE
# =====================
def get_ignored_version():
    if os.path.exists(IGNORED_VERSION_FILE):
        return open(IGNORED_VERSION_FILE).read().strip()
    return None

def check_update():
    try:
        url = "https://raw.githubusercontent.com/Cuby405/LocalPyChat/main/version.txt"
        with urllib.request.urlopen(url, timeout=3) as r:
            online = r.read().decode().strip()

        ignored = get_ignored_version()
        if online != APP_VERSION and online != ignored:
            return online
    except:
        pass
    return None

# =====================
# TK INIT
# =====================
root = tk.Tk()
root.withdraw()

# =====================
# CONFIG
# =====================
config = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v

# =====================
# LOGIN
# =====================
USER = simpledialog.askstring("Usuario", "Nombre de usuario:")
if not USER:
    exit()

pwd = simpledialog.askstring("Contraseña", "Contraseña:", show="*")
if not pwd:
    exit()

PWD_HASH = hash_pwd(pwd)

COLOR = config.get("color")

if not COLOR:
    color = colorchooser.askcolor(title="Elige tu color de usuario")
    if color[1]:  # color[1] es el HEX
        COLOR = color[1]
    else:
        COLOR = "#ffffff"

SERVER_IP = config.get("ip")

if not SERVER_IP:
    SERVER_IP = simpledialog.askstring("Servidor", "IP del servidor:")
    if not SERVER_IP:
        exit()

with open(CONFIG_FILE, "w") as f:
    f.write(f"user={USER}\n")
    f.write(f"pwd_hash={PWD_HASH}\n")
    f.write(f"color={COLOR}\n")
    f.write(f"ip={SERVER_IP}\n")

# =====================
# SOCKET
# =====================
sock = None
user_colors = {}

loading_history = True


def finish_loading_history():
    global loading_history
    loading_history = False

def connect_to_server():
    global sock, loading_history
    try:
        loading_history = True
        sock = socket.socket()
        sock.connect((SERVER_IP, PORT))
        sock.send(f"__LOGIN__:{USER}|{PWD_HASH}|{COLOR}".encode())

        # Esperar un pequeño momento para que cargue el historial
        root.after(1000, finish_loading_history)

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo conectar:\n{e}")

def receive_messages():
    while True:
        try:
            msg = sock.recv(1024).decode()
            for line in msg.split("\n"):
                if not line.strip():
                    continue

                if line.startswith("__USERS__"):
                    users_raw = line.split(":", 1)[1]
                    user_colors.clear()
                    for u in users_raw.split(","):
                        if "|" in u:
                            n, c = u.split("|", 1)
                            user_colors[n] = c

                    users_area.configure(state="normal")
                    users_area.delete(1.0, tk.END)
                    for u, c in user_colors.items():
                        users_area.insert(tk.END, u + "\n", u)
                        users_area.tag_config(u, foreground=c)
                    users_area.configure(state="disabled")
                    continue

                chat_area.configure(state="normal")
                if ":" in line:
                    u, m = line.split(":", 1)
                    chat_area.insert(tk.END, f"{u}: ", u)
                    chat_area.tag_config(u, foreground=user_colors.get(u, "#fff"))
                    chat_area.insert(tk.END, m.strip() + "\n")
                else:
                    chat_area.insert(tk.END, line + "\n")
                chat_area.configure(state="disabled")
                chat_area.see(tk.END)

                # 🔔 NOTIFICACIÓN
                if u != USER:
                    notify(current_chat, u, m)

        except:
            time.sleep(1)

def send_message(event=None):
    msg = message_entry.get().strip()
    if msg:
        sock.send(f"{USER}:{msg}".encode())
        message_entry.delete(0, tk.END)

def clear_chat():
    chat_area.configure(state="normal")
    chat_area.delete(1.0, tk.END)
    chat_area.configure(state="disabled")

# =====================
# CHATS (SIDEBAR)
# =====================
chats = {}
current_chat = "Default"

if os.path.exists(CHATS_FILE):
    chats = json.load(open(CHATS_FILE))

def save_chats():
    json.dump(chats, open(CHATS_FILE, "w"), indent=2)

if "Default" not in chats:
    chats["Default"] = SERVER_IP
    save_chats()

def switch_chat(name):
    global SERVER_IP, current_chat
    current_chat = name
    SERVER_IP = chats[name]
    clear_chat()
    try:
        sock.close()
    except:
        pass
    threading.Thread(target=connect_to_server, daemon=True).start()

def add_chat():
    name = simpledialog.askstring("Nuevo chat", "Nombre del chat:")
    ip = simpledialog.askstring("IP", "IP del servidor:")
    if name and ip:
        chats[name] = ip
        save_chats()
        refresh_sidebar()

def edit_chat(name):
    if name == "Default":
        # Solo permitir cambiar IP
        new_ip = simpledialog.askstring(
            "Editar IP",
            "Nueva IP:",
            initialvalue=chats[name]
        )
        if not new_ip:
            return

        chats[name] = new_ip

    else:
        new_name = simpledialog.askstring(
            "Editar chat",
            "Nuevo nombre:",
            initialvalue=name
        )
        if not new_name:
            return

        new_ip = simpledialog.askstring(
            "Editar IP",
            "Nueva IP:",
            initialvalue=chats[name]
        )
        if not new_ip:
            return

        chats.pop(name)
        chats[new_name] = new_ip

    save_chats()
    refresh_sidebar()

def delete_chat(name):
    if name == "Default":
        messagebox.showwarning("Error", "No puedes borrar el chat Default")
        return

    if messagebox.askyesno("Borrar", f"¿Seguro que quieres borrar '{name}'?"):
        if current_chat == name:
            switch_chat("Default")

        chats.pop(name, None)
        save_chats()
        refresh_sidebar()

# =====================
# UI
# =====================
root.deiconify()
root.title(f"PyChat - {USER}")
root.geometry("950x500")
root.configure(bg="black")

sidebar = tk.Frame(root, bg="#111", width=180)
sidebar.pack(side=tk.LEFT, fill=tk.Y)

tk.Button(sidebar, text="Añadir nuevo chat", command=add_chat).pack(fill=tk.X)
tk.Button(sidebar, text="Reportar bug", command=open_bug_report).pack(fill=tk.X)

chats_frame = tk.Frame(sidebar, bg="#111")
chats_frame.pack(fill=tk.Y, expand=True)

def refresh_sidebar():
    for w in chats_frame.winfo_children():
        w.destroy()

    for name in chats:
        row = tk.Frame(chats_frame, bg="#111")
        row.pack(fill=tk.X, pady=2)

        # Botón principal (entrar al chat)
        tk.Button(
            row,
            text=name,
            command=lambda n=name: switch_chat(n),
            anchor="w"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Botón editar
        tk.Button(
            row,
            text="✏",
            width=3,
            command=lambda n=name: edit_chat(n)
        ).pack(side=tk.LEFT)

        # Botón borrar
        tk.Button(
            row,
            text="🗑",
            width=3,
            command=lambda n=name: delete_chat(n)
        ).pack(side=tk.LEFT)

refresh_sidebar()

main_frame = tk.Frame(root, bg="black")
main_frame.pack(fill=tk.BOTH, expand=True)

chat_area = scrolledtext.ScrolledText(main_frame, bg="black", fg="white", state="disabled")
chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

users_area = scrolledtext.ScrolledText(main_frame, width=20, bg="black", fg="white", state="disabled")
users_area.pack(side=tk.RIGHT, fill=tk.Y)

message_frame = tk.Frame(root, bg="black")
message_frame.pack(fill=tk.X)

message_entry = tk.Entry(message_frame, bg="#222", fg="white")
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
message_entry.bind("<Return>", send_message)

tk.Button(message_frame, text="Enviar", command=send_message).pack(side=tk.LEFT)

# =====================
# MODO OSCURO / CLARO
# =====================
dark_mode = True  # por defecto en oscuro

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode

    if dark_mode:
        colors = {
            "bg_root": "black",
            "bg_frame": "black",
            "fg_text": "white",
            "bg_entry": "#222",
            "bg_sidebar": "#111",
            "fg_sidebar": "white"
        }
    else:
        colors = {
            "bg_root": "white",
            "bg_frame": "white",
            "fg_text": "black",
            "bg_entry": "#eee",
            "bg_sidebar": "#ddd",
            "fg_sidebar": "black"
        }

    # aplicar colores
    root.configure(bg=colors["bg_root"])
    main_frame.configure(bg=colors["bg_frame"])
    message_frame.configure(bg=colors["bg_frame"])
    sidebar.configure(bg=colors["bg_sidebar"])
    chat_area.configure(bg=colors["bg_frame"], fg=colors["fg_text"])
    users_area.configure(bg=colors["bg_frame"], fg=colors["fg_text"])
    message_entry.configure(bg=colors["bg_entry"], fg=colors["fg_text"])

# Añadir botón
tk.Button(sidebar, text="Toggle Modo Claro/Oscuro", command=toggle_theme).pack(fill=tk.X)

# =====================
# NOTIFICACIONES
# =====================
notifications_enabled = True

def toggle_notifications():
    global notifications_enabled
    notifications_enabled = not notifications_enabled
    status = "activadas" if notifications_enabled else "desactivadas"
    messagebox.showinfo("Notificaciones", f"Notificaciones {status}")

def notify(chat, user, msg):
    if loading_history:
        return

    if not notifications_enabled:
        return

    if user == USER:
        return

    try:
        from plyer import notification
        notification.notify(
            title=f"{chat} - {user}",
            message=msg,
            timeout=5
        )
    except:
        pass

# Añadir botón
tk.Button(sidebar, text="Activar/Desactivar Notifs", command=toggle_notifications).pack(fill=tk.X)

# =====================
# START
# =====================
threading.Thread(target=connect_to_server, daemon=True).start()
threading.Thread(target=receive_messages, daemon=True).start()

root.mainloop()
