# 🚀 [Proyecto Visual Ansible]

-Crear una capa visual que facilite la utilización de ANSIBLE en las aulas. 
El usuario podrá descargar la imagen Docker, lanzar el contenedor de VISUAL ANSIBLE y automatizar la instalación de programas en los ordenadores del aula, sea Windows o Linux.

---

## 👥 Equipo y Colaboradores

¡Las personas que hacen posible este proyecto!

| Nombre | Rol / Especialidad | GitHub |
| :--- | :--- | :--- |
| **Juan Fco. Entrena Garrido** | xxxxx | [@JuanEntrena18] |
| **Diego Toribio Perea** | xxxxx | [@DIEGO1ASIRC] |
| **Daniel Palacios Melguizo** |xxxxx | [@dpalmel1312] |
| **Marina Jiménez Egea** | xxxxx | [@Marjieg] |
| **Félix David Romero López** | xxxxx | [@felixdavid28] |

## 📖 Tabla de Contenidos

* [Descripción del Proyecto](#-descripción-del-proyecto)
* [Secciones Principales](#-secciones-principales)
* [Equipo y Colaboradores](#-equipo-y-colaboradores)
* [Primeros Pasos (Cómo Empezar)](#-primeros-pasos)
* [Cómo Contribuir](#-cómo-contribuir)

---

## 📝 Descripción del Proyecto

Aquí puedes extenderte un poco más. ¿Qué problema soluciona este proyecto? ¿Cuál es el objetivo final? ¿Qué tecnologías clave se están utilizando (ej. React, Python, Node.js, etc.)?

## 📂 Secciones Principales

Aquí se detallan las partes o módulos clave que componen el proyecto. Esto ayuda a que todos entiendan la arquitectura general.

* **/seccion-1 (Ej. Autenticación de Usuarios):**
    * Descripción: Manejo del registro, inicio de sesión y perfiles de usuario.
    * Responsable(s): [Nombre o @usuario-github]

* **/seccion-2 (Ej. Dashboard Principal):**
    * Descripción: Interfaz principal donde los usuarios ven sus datos.
    * Responsable(s): [Nombre o @usuario-github]

* **/seccion-3 (Ej. API / Backend):**
    * Descripción: La lógica del servidor que procesa los datos y se conecta a la base de datos.
    * Responsable(s): [Nombre o @usuario-github]

* **/seccion-4 (Ej. Documentación):**
    * Descripción: Documentación técnica y guías de usuario.
    * Responsable(s): [Nombre o @usuario-github]

---

## 🏁 Primeros Pasos (Cómo Empezar)

Instrucciones claras para que cualquier miembro del equipo pueda poner en marcha el proyecto en su máquina local.

### Prerrequisitos para replicar el servidor UBUNTU del proyecto

Paso 1: Seguridad Básica
Esto es lo primero que debes hacer, antes de instalar nada más.
Crear un Usuario no-root: Nunca uses root para las operaciones diarias.
```bash
adduser visualansible (pass: visualansible)
usermod -aG sudo visualansible
Configurar SSH con Claves: Desactiva el login con contraseña.
Copia tu clave pública local (~/.ssh/id_rsa.pub) al archivo ~/.ssh/authorized_keys del nuevo usuario en el servidor.
Edita /etc/ssh/sshd_config y cambia PasswordAuthentication no.
Reinicia SSH: sudo systemctl restart sshd.
```
Activar el Firewall (UFW): Cierra todos los puertos excepto los necesarios.
```bash
sudo ufw allow OpenSSH (o sudo ufw allow 22/tcp)
sudo ufw allow http (Puerto 80)
sudo ufw allow https (Puerto 443)
sudo ufw enable
```
Paso 2: Instalar el "Motor" (Ansible)
Ansible se ejecuta sobre Python, que Ubuntu 22.04 ya incluye. La mejor forma de instalar Ansible es usando su PPA oficial para tener la última versión estable.
```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible-core (o ansible para el paquete completo)
```
Paso 3: Instalar la "Pila de Backend" (API y BBDD)
Aquí debes tomar una decisión tecnológica para tu API: ¿Node.js o Python?
Opción (Python - con Flask o FastAPI):
```bash
sudo apt install python3-pip python3-venv
mkdir -p /opt/ansible-visual/api
cd /opt/ansible-visual/api
python3 -m venv venv
source venv/bin/activate
pip install gunicorn fastapi uvicorn
```
Si da error por permisos al haber creado la carpeta como usuario privilegiado
```bash
deactivate
sudo chown -R docker:docker /opt/ansible-visual
cd /opt/ansible-visual/api
source venv/bin/activate
pip install gunicorn fastapi uvicorn
```
Si da error por permisos
Para la Base de Datos (recomiendo PostgreSQL):
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql (Entra a la consola de Postgres).
Dentro de psql:
CREATE DATABASE ansible_visual;
CREATE USER visual_admin WITH ENCRYPTED PASSWORD '[tu_clave_segura]';
GRANT ALL PRIVILEGES ON DATABASE ansible_visual TO visual_admin;
\q (Para salir).


### Instalación

1.  Clona este repositorio:
    ```bash
    git clone https://github.com/JuanEntrena18/proyecto_ansible.git
    cd proyecto_ansible
    ```

## 🤝 Cómo Contribuir

Para mantener el orden, seguimos un flujo de trabajo específico:

1.  **Nunca trabajes directamente en `main`**.
2.  Crea una nueva rama para tu tarea: `git checkout -b feature/nombre-de-tu-tarea`.
3.  Haz tus cambios y guarda (commit) con mensajes claros.
4.  Sube tu rama a GitHub: `git push origin feature/nombre-de-tu-tarea`.
5.  Abre un **Pull Request** (PR) dirigido a la rama `main`.
6.  Asigna al menos a un miembro del equipo como **revisor**.
7.  Una vez aprobado, se fusionará (merge) con `main`.

---
