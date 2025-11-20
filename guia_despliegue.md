📘 Ansible Visual - Guía de Despliegue (MVP Fase 1)

Objetivo: Crear un servidor que aloje un editor visual (estilo Unreal Engine) capaz de escanear la red local, detectar sistemas operativos y generar nodos automáticamente.

Requisitos:

    Servidor Ubuntu 22.04 LTS (Máquina Virtual o Física).

    Conexión a internet.

    Importante: Si usas VirtualBox, configura la red en "Adaptador Puente" (Bridged) para poder escanear tu red local real.

1. Preparación del Sistema y Dependencias

Instalaremos Nginx (Web Server), Python (Backend), Ansible (Motor) y Nmap (Escáner).

```
# 1. Actualizar repositorios
sudo apt update && sudo apt upgrade -y

# 2. Instalar herramientas básicas
sudo apt install -y software-properties-common curl git ufw

# 3. Instalar Ansible (Motor de IaC)
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible-core

# 4. Instalar Nginx (Servidor Web y Proxy)
sudo apt install -y nginx

# 5. Instalar Python venv y Nmap (Escáner de red)
sudo apt install -y python3-venv nmap
```
2. Configuración del Backend (API Python)

El "cerebro" del sistema. Usaremos FastAPI para ejecutar comandos de sistema.

2.1. Crear directorios y entorno virtual

```
# 1. Crear carpeta de la API (cambia 'tu_usuario' por tu usuario real, ej: juan)
sudo mkdir -p /opt/ansible-visual/api
sudo chown -R $USER:$USER /opt/ansible-visual

# 2. Crear entorno virtual aislado
cd /opt/ansible-visual/api
python3 -m venv venv

# 3. Activar entorno e instalar librerías
source venv/bin/activate
pip install fastapi uvicorn gunicorn
deactivate
```
2.2. Código del Backend (main.py)

Crea el archivo de la aplicación:
```
nano /opt/ansible-visual/api/main.py
```
Pega el siguiente código:
from fastapi import FastAPI
import subprocess
import re

app = FastAPI()

@app.get("/")
def read_root():
    return {"estado": "OK", "mensaje": "Backend Ansible Visual Activo"}

@app.get("/scan")
def scan_network(subnet: str = "192.168.1.0/24"):
    try:
        # Validación básica de seguridad
        if not re.match(r"^[0-9./]+$", subnet):
             return {"estado": "ERROR", "detalle": "Formato de red inválido"}

        # Ejecutamos Nmap con detección de versiones (-sV) y sin ping (-Pn)
        # Usamos ruta absoluta /usr/bin/nmap por seguridad
        comando = ["/usr/bin/nmap", "-p", "22", "-sV", "-Pn", "--open", "-oG", "-", subnet]
        
        resultado = subprocess.run(comando, capture_output=True, text=True)
        
        equipos_encontrados = []

        for linea in resultado.stdout.splitlines():
            # Buscamos líneas de host con puerto 22 abierto
            if "Host:" in linea and "22/open" in linea:
                # 1. Extraer IP
                ip_match = re.search(r'Host: ([0-9.]+)', linea)
                if ip_match:
                    ip = ip_match.group(1)
                    
                    # 2. Detectar S.O. basado en el banner SSH
                    os_detectado = "Linux Genérico"
                    icon_os = "fas fa-server" 

                    version_match = re.search(r'//ssh//(.*?)/', linea)
                    if version_match:
                        banner = version_match.group(1).lower()
                        if "ubuntu" in banner:
                            os_detectado = "Ubuntu Server"
                            icon_os = "fab fa-ubuntu"
                        elif "debian" in banner:
                            os_detectado = "Debian"
                            icon_os = "fab fa-linux"
                        elif "raspbian" in banner:
                            os_detectado = "Raspberry Pi"
                            icon_os = "fab fa-raspberry-pi"
                        elif "windows" in banner:
                            os_detectado = "Windows (SSH)"
                            icon_os = "fab fa-windows"
                    
                    equipos_encontrados.append({
                        "ip": ip,
                        "os": os_detectado,
                        "icon": icon_os
                    })

        return {"estado": "OK", "equipos": equipos_encontrados}

    except Exception as e:
        print(f"Error interno: {e}")
        return {"estado": "ERROR", "detalle": str(e)}
```
2.3. Configurar Servicio Systemd

Para que la API se ejecute siempre en segundo plano.
