import urllib.request
import zipfile
import sys
import os
import time
import shutil

ZIP_URL = "https://github.com/Cuby405/LocalPyChat/raw/main/client.zip"

def main():
    time.sleep(2)  # esperar a que el cliente se cierre

    zip_path = "update.zip"

    urllib.request.urlretrieve(ZIP_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(".")

    os.remove(zip_path)

    # limpiar versión ignorada (ya no aplica)
    ignored = os.path.join(".data", "ignored_version.txt")
    if os.path.exists(ignored):
        os.remove(ignored)

    # reiniciar programa
    os.execv(sys.executable, [sys.executable, "client.py"])


if __name__ == "__main__":
    main()