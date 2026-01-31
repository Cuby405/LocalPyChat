# LocalPyChat

Chat local escrito en Python con interfaz gráfica (Tkinter), pensado para redes privadas
(LAN / Hamachi / VPN).

Incluye sistema de login, colores por usuario y actualizaciones automáticas desde GitHub.

---

## ✨ Características

- Cliente gráfico en Python (Tkinter)
- Servidor compatible con Linux y Windows
- Usuarios con contraseña (hash)
- Colores personalizados por usuario
- Lista de usuarios conectados
- Historial de mensajes
- Sistema de auto-actualización
- Ejecutables `.exe` para Windows

---

## 📦 Estructura del proyecto

client.py        Cliente gráfico

server.py        Servidor

updater.py       Sistema de actualizaciones

version.txt      Versión remota disponible

client.spec      Configuración PyInstaller (cliente)

server.spec      Configuración PyInstaller (servidor)

tools/            Scripts auxiliares

---

## 🚀 Uso rápido

### Servidor (Linux o Windows)

```
bash
python server.py
```

O usando `server.exe` si existe.

### Cliente (Windows)

Ejecuta `client.exe` o:

```
bash
python client.py
```

## 🔄 Actualizaciones

El cliente comprueba automáticamente la versión disponible usando:

`version.txt`

Si hay una versión nueva, se notifica al usuario y se descarga desde  **Releases** .

---

## 🛠️ Compilar ejecutables

Requiere PyInstaller:

```
bash
pip install pyinstaller
pyinstaller client.spec
pyinstaller server.spec
```

Los ejecutables se generarán en la carpeta `dist/`.
