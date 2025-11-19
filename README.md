## 🟦 Ansible Visual Project
Objetivo: Crear una interfaz visual basada en nodos (estilo Blueprints de Unreal Engine) para generar y ejecutar playbooks de Ansible, simplificando la infraestructura como código (IaC).

## 👥 Equipo y Colaboradores

¡Las personas que hacen posible este proyecto!

| Nombre | Rol / Especialidad | GitHub |
| :--- | :--- | :--- |
| **Juan Fco. Entrena Garrido** | xxxxx | [@JuanEntrena18] |
| **Diego Toribio Perea** | xxxxx | [@DIEGO1ASIRC] |
| **Daniel Palacios Melguizo** |xxxxx | [@dpalmel1312] |
| **Marina Jiménez Egea** | xxxxx | [@Marjieg] |
| **Félix David Romero López** | xxxxx | [@felixdavid28] |

## 🚀 Fase 1: Infraestructura y Arquitectura Base
En esta fase se ha establecido los cimientos del servidor, la seguridad y la tubería de comunicación completa entre el Frontend y el Backend. Se ha configurado un entorno de producción "Bare Metal" en Ubuntu 22.04 antes de la futura contenerización con Docker.

### 🏗️ Stack Tecnológico (Estado Actual)
OS: Ubuntu Server 22.04 LTS.

Web Server / Proxy: Nginx.

Backend API: Python (FastAPI + Uvicorn + Gunicorn).

Process Manager: Systemd.

IaC Engine: Ansible Core.

Frontend (Base): HTML/JS (Sirviendo estáticos vía Nginx).

### ⚙️ Arquitectura del Sistema
El sistema utiliza Nginx como punto de entrada único (Reverse Proxy) para gestionar tanto la entrega de la aplicación visual como las peticiones a la API, evitando problemas de CORS y simplificando la exposición de puertos.

´´´
graph LR
    User(Navegador Usuario) -- Puerto 80 --> Nginx[Nginx Server]
    
    subgraph Server [Ubuntu 22.04]
        Nginx -- / (Raíz) --> Static[Archivos Frontend]
        Nginx -- /api/ --> Proxy[Reverse Proxy]
        Proxy -- Puerto 8000 --> Gunicorn[Gunicorn + Uvicorn]
        
        subgraph Backend [Entorno Virtual Python]
            Gunicorn --> FastAPI[API FastAPI]
            FastAPI --> Ansible[Motor Ansible]
        end
    end
´´´
---
