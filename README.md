# Visual/\nsible - Gestión de Aulas con Ansible

Interfaz visual basada en nodos para gestionar y ejecutar playbooks de Ansible en aulas informáticas. Escanea la red, detecta equipos Windows y Linux, y permite ejecutar tareas de automatización con un simple arrastrar y soltar.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | HTML5 + jQuery + AdminLTE 3 + Drawflow |
| Backend | Python 3.12 + FastAPI + Uvicorn/Gunicorn |
| Proxy | Nginx (con HTTPS y headers de seguridad) |
| Automatización | Ansible Core + WinRM + SSH |
| Escaneo | Nmap |
| Contenedores | Docker + Docker Compose |
| Seguridad | JWT + bcrypt + Fernet + HTTPS |

## Arquitectura

```mermaid
graph TD
    User([Navegador]) -- "HTTPS (:443)" --> Nginx{Nginx}

    subgraph "Servidor Ubuntu"
        Nginx --> Frontend["<b>Frontend (estático)</b><br/>/var/www/.../html"]
        Nginx -- "Proxy Pass" --> Backend["<b>Backend API (:8000)</b><br/>FastAPI + Gunicorn"]

        subgraph "Core Engine"
            Backend --> Nmap["<b>Nmap</b><br/>(Network Scan)"]
            Backend --> Ansible["<b>Ansible</b><br/>(Automation)"]
            Backend --> Logs[("<b>Logs</b><br/>(History)")]
        end
    end

    subgraph "Infraestructura"
        Ansible -- "SSH (:22)" --> Linux["Hosts Linux"]
        Ansible -- "WinRM (:5985)" --> Windows["Hosts Windows"]
    end

    %% Estilos
    style Nginx fill:#f9f,stroke:#333,stroke-width:2px
    style Backend fill:#bbf,stroke:#333,stroke-width:2px
    style User fill:#fff,stroke:#333
```
```mermaid
graph TD
    %% Título General
    title[Arquitectura General: Visual/Ansible]

    %% Definición de Nodos Principales
    Proxy[Capa Proxy]
    Logica[Capa Lógica]
    Continuidad[Capa de Continuidad]
    Datos[Persistencia de Datos]

    %% Flujos de Comunicación y Dependencia
    Proxy -->|Tráfico Externo/Seguridad| Logica
    Logica -->|Peticiones/Operaciones/Ansible/Nmap| Datos
    Continuidad -->|Automatización de Backups| Datos
    Continuidad -.->|Estado/Orquestación (Opcional)| Logica
    
    %% Relación Lógica Directa (Ejemplo: Logs o Config)
    Logica -.->|Logs/Config Indirecta| Datos

    %% Estilos de los Nodos (Opcionales, Mermaid aplica estilos básicos por defecto)
    style Proxy fill:#f9f,stroke:#333,stroke-width:2px;
    style Logica fill:#ccf,stroke:#333,stroke-width:2px;
    style Continuidad fill:#ff9,stroke:#333,stroke-width:2px;
    style Datos fill:#9f9,stroke:#333,stroke-width:2px;
    style title fill:none,stroke:none,font-size:18px,font-weight:bold;
```

```mermaid
flowchart TD
    %% Título General
    Titulo["Arquitectura Completa del Sistema Visual/Ansible"]

    %% --------------------------------------------------------
    %% 1. CAPA PROXY
    %% --------------------------------------------------------
    subgraph CapaProxy ["1. CAPA PROXY (Puerta de Entrada)"]
        direction TB
        Nginx["Nginx (Reverse Proxy)"]
        Seguridad["Escudo: Rate Limiting & SSL/TLS"]
        
        Nginx --- Seguridad
    end

    %% --------------------------------------------------------
    %% 2. CAPA LÓGICA
    %% --------------------------------------------------------
    subgraph CapaLogica ["2. CAPA LÓGICA (Orquestación y API)"]
        direction TB
        Backend["Backend FastAPI (Privilegios NET_RAW)"]
        Motores["Motores de Ejecución: Ansible + Nmap"]
        Creds["Inyección de Clave Maestra (KeePass)"]
        
        Backend --- Motores
        Backend --- Creds
    end

    %% --------------------------------------------------------
    %% 3. CAPA DE PERSISTENCIA
    %% --------------------------------------------------------
    subgraph CapaDatos ["3. CAPA DE PERSISTENCIA (Volúmenes Host)"]
        direction TB
        Carpetas["Directorios Físicos: /data, /config, /ansible"]
        BasesDatos["Bases de Datos: usuarios.db e inventory.json"]
        
        Carpetas --- BasesDatos
    end

    %% --------------------------------------------------------
    %% 4. CAPA DE CONTINUIDAD
    %% --------------------------------------------------------
    subgraph CapaContinuidad ["4. CAPA DE CONTINUIDAD (Protección DRP)"]
        direction TB
        Alpine["Servicio Alpine (Aislado)"]
        Scripts["Ejecución Cron: backup.sh + Exportación SCP"]
        
        Alpine --- Scripts
    end

    %% ========================================================
    %% RELACIONES VERTICALES (Fuerzan el diseño de Arriba a Abajo)
    %% ========================================================
    CapaProxy == "Enruta peticiones seguras hacia la API" ==> CapaLogica
    CapaLogica == "Actualiza inventarios y lee credenciales" ==> CapaDatos
    CapaContinuidad -. "Comprime datos en modo Solo Lectura" .-> CapaDatos

    %% ========================================================
    %% ESTILOS VISUALES (Optimizados para GitHub)
    %% ========================================================
    style CapaProxy fill:#e0f2fe,stroke:#0284c7,stroke-width:3px,color:#0f172a
    style CapaLogica fill:#ede9fe,stroke:#7c3aed,stroke-width:3px,color:#0f172a
    style CapaDatos fill:#dcfce7,stroke:#16a34a,stroke-width:3px,color:#0f172a
    style CapaContinuidad fill:#fef9c3,stroke:#ca8a04,stroke-width:3px,color:#0f172a
    style Titulo fill:none,stroke:none,font-size:22px,font-weight:bold
```

## Funcionalidades

- **Escaneo de red**: Detección automática de equipos Windows y Linux via Nmap
- **Playbooks predefinidos**: 10 plantillas listas para usar (instalación de software, firewall, usuarios, Docker, XAMPP, etc.)
- **Ejecución drag and drop**: Arrastra un playbook sobre un host y se ejecuta al instante
- **Streaming en tiempo real**: La salida de Ansible se muestra en el navegador mientras se ejecuta
- **Playbooks personalizados**: Crea y guarda tus propios playbooks desde la interfaz
- **Multiplataforma**: Soporta hosts Windows (WinRM) y Linux (SSH) simultaneamente
- **Logs de auditoría**: Historial completo de todas las ejecuciones

## Seguridad

- **Autenticación JWT**: Dos roles: `admin` (control total) y `operador` (solo lectura)
- **HTTPS obligatorio**: Puerto 80 redirige a 443 con certificado SSL
- **Credenciales cifradas**: `credentials.json` se cifra en disco con Fernet
- **Headers de seguridad**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **Contraseñas nunca en cliente**: Las contraseñas de los hosts viajan solo del frontend al backend, nunca al reves
- **Validación de entrada**: Regex en IPs, rutas, nombres de archivo y usuarios
- **Tokens efímeros**: JWT con expiración de 24 horas

## Despliegue Rápido (Docker)

```bash
# Clonar repositorio
git clone https://github.com/JuanEntrena18/proyecto_ansible
cd proyecto_ansible/github

# Generar clave de cifrado para credenciales
export CREDENTIALS_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Construir y arrancar
sudo docker compose up -d --build
```

Accede a `https://<IP-del-servidor>` con usuario `admin` y contraseña `admin`.

## API REST

| Metodo | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| POST | `/login` | - | Inicio de sesión (devuelve JWT) |
| GET | `/me` | JWT | Información del usuario |
| GET | `/scan?subnet=X.X.X.X/XX` | JWT | Escanea una subred con Nmap |
| GET | `/playbooks` | JWT | Lista los playbooks disponibles |
| GET | `/playbooks/{tipo}/{nombre}` | JWT | Lee el contenido de un playbook |
| POST | `/playbooks` | Admin | Guarda un playbook personalizado |
| POST | `/execute` | Admin | Ejecuta un playbook en uno o varios hosts |
| GET | `/credentials` | Admin | Obtiene los usuarios configurados |
| POST | `/credentials` | Admin | Guarda credenciales de acceso a hosts |
| GET | `/logs` | Admin | Historial de ejecuciones |

## Playbooks Disponibles

| Playbook | SO | Descripción |
|----------|----|-------------|
| `instalar_software` | Linux + Windows | Instala paquetes desde group_vars |
| `instalar_docker` | Linux | Instala Docker CE |
| `instalar_xampp` | Linux + Windows | Instala XAMPP / LAMP |
| `instalar_libreoffice` | Linux + Windows | Instala LibreOffice |
| `crear_usuario` | Linux + Windows | Crea usuario `alumno` |
| `configurar_acceso` | Linux + Windows | Configura SSH y WinRM |
| `configurar_firewall` | Linux + Windows | Abre puertos en firewall |
| `actualizar_sistema` | Linux + Windows | Actualiza paquetes del sistema |
| `renombrar_equipos` | Linux + Windows | Renombra equipos segun IP |
| `desinstalar_todo` | Linux + Windows | Desinstala todo el software instalado |

## Estructura del Proyecto

```
github/
+-- backend/
|   +-- main.py              # API FastAPI (JWT + cifrado)
|   +-- requirements.txt     # Dependencias Python
|   +-- Dockerfile           # Imagen del backend
+-- frontend/
|   +-- index.html           # Interfaz de usuario
+-- config/
|   +-- nginx.conf           # Proxy HTTPS con seguridad
|   +-- ssl/                 # Certificados SSL
|   +-- credentials.json     # Credenciales cifradas
+-- ansible/
|   +-- ansible.cfg          # Configuracion de Ansible
|   +-- inventory/           # Inventarios y group_vars
|   +-- playbooks/
|   |   +-- templates/       # Playbooks predefinidos
|   |   +-- custom/          # Playbooks del usuario
|   +-- roles/               # Roles de Ansible
|   +-- logs/                # Historial de ejecuciones
+-- scripts/
|   +-- backup.sh            # Backup automático diario
+-- docker-compose.yml       # Orquestación de contenedores
+-- README.md
```

## Variables de Entorno

| Variable | Descripción | Obligatoria |
|----------|-------------|-------------|
| `CREDENTIALS_KEY` | Clave Fernet para cifrar credentials.json | Recomendada (se autogenera si no existe) |

## Despliegue Tradicional (sin Docker)

Consulta la [Guia de Despliegue](Guia_despliegue_0_5.ipynb) para instalación en Ubuntu Server 22.04/24.04 sin Docker.

## Equipo

| Nombre | Rol | GitHub |
|--------|-----|--------|
| Juan Fco. Entrena Garrido | Desarrollo | [@JuanEntrena18](https://github.com/JuanEntrena18) |
| Diego Toribio Perea | Desarrollo | [@DiegoToribio06](https://github.com/DiegoToribio06) |
| Daniel Palacios Melguizo | Desarrollo | [@dpalmel1312](https://github.com/dpalmel1312) |
| Marina Jimenez Egea | Desarrollo | [@Marjieg](https://github.com/Marjieg) |
| Felix David Romero Lopez | Desarrollo | [@felixdavid28](https://github.com/felixdavid28) |
