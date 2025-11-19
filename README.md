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

https://mermaidchart.com/play?utm_source=mermaid_live_editor&utm_medium=share#pako:eNptUdtu4jAQ_RVrnlotpbm4weRhJXZ7UaW2QlTsQ5N9MMmUWAUbOTaCIj5pv2J_bCdJaWm1I9k6xz7njEfeQWFKhBTmVq4qdjfJNaOa1mhPHuQa57I0lqiXVplTdnbGxh6tM0wERL6zh7nSm6zd2SPaNdrfXUK3137WBXd3LJvOvHaeRVE_4G_KproASj9nJxP598_raZv-6KRTRTayRaXWpmbX1miHuvyvU67UeesaW7PZZhOkhjV27MjQ8k-DBN0oN16rwlidHQD7xqbrFh3ZP9D7bD9k8UKPYtmVdiQ27JeyzssFG29dZY7NTb2nNz2vZe1G49uM1gF_kb-dtuqRrtVsgdm9oT4HdqSnR3SEAPToS1UJqbMee7BEu5QNhV0jycFVuMQcUoIlPku_cDnkek-2ldRPxiwPTmv8vIL0WS5qYn5VSoeXStLoHxLqh_anoa-FNAx4mwHpDjaQxkk_4XzA4zCJw-EgSHqwJVEc9qOBSER0EcRJwodi34PXtmvQH3IeiTAR_CIUIorE_h-Qfsxg

---
