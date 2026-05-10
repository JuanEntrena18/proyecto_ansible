# main.py
# Este es el backend del proyecto. Basicamente es una API hecha con FastAPI
# que se encarga de escanear la red local con nmap, listar los playbooks
# que tenemos guardados y ejecutarlos contra las maquinas que el usuario
# elija desde la interfaz web. Para Linux usa SSH y para Windows WinRM.
 
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import subprocess, re, os, yaml, tempfile, json, datetime
 
app = FastAPI()
 
# rutas dentro del contenedor donde tenemos todo montado
ANSIBLE_DIR   = "/opt/ansible-visual/ansible"
TEMPLATES_DIR = ANSIBLE_DIR + "/playbooks/templates"
CUSTOM_DIR    = ANSIBLE_DIR + "/playbooks/custom"
CREDS_FILE    = "/opt/ansible-visual/credentials.json"
LOG_FILE      = ANSIBLE_DIR + "/logs/executions.log"
VAULT_PASS    = "/opt/ansible-visual/vault_password"
os.makedirs(CUSTOM_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
 
 
# --- Modelos de datos para las peticiones ---
 
class PlaybookData(BaseModel):
    nombre: str
    contenido: str
 
class HostInfo(BaseModel):
    ip: str
    os: str = "Linux"
 
class Credenciales(BaseModel):
    usuario: str
    password: str
 
class ExecuteData(BaseModel):
    playbook: str
    tipo: str = "templates"
    hosts: List[HostInfo]
    credenciales: Credenciales
 
# Modelo para guardar credenciales desde la web
# Todos los campos son opcionales: el frontend solo manda los que han cambiado
class CredencialesGuardar(BaseModel):
    linux_user: Optional[str] = None
    linux_pass: Optional[str] = None
    win_user: Optional[str] = None
    win_pass: Optional[str] = None
 
 
# --- Funciones de validacion ---
# Aqui metemos comprobaciones para que no nos cuelen nombres raros
# ni rutas peligrosas. Basico pero necesario.
 
def nombre_ok(nombre):
    """Comprueba que el nombre del archivo no tenga cosas raras tipo ../ o barras"""
    return bool(nombre and ".." not in nombre and "/" not in nombre
                and "\\" not in nombre and re.match(r"^[a-zA-Z0-9_\-]+\.yml$", nombre))
 
def ip_ok(ip):
    """Formato IPv4 basico: cuatro grupos de numeros separados por puntos"""
    return bool(re.match(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$", ip))
 
def ruta_segura(ruta, directorio_base):
    """Esto lo vimos en la asignatura de seguridad: evitar path traversal"""
    return os.path.realpath(ruta).startswith(os.path.realpath(directorio_base))
 
 
def detectar_os_playbook(ruta):
    """Lee un playbook y detecta a que SO va dirigido segun las directivas hosts:"""
    try:
        with open(ruta) as f:
            contenido = f.read()
        tiene_win = "hosts: windows" in contenido
        tiene_linux = "hosts: linux" in contenido
        if tiene_win and tiene_linux:
            return "ambos"
        elif tiene_win:
            return "windows"
        elif tiene_linux:
            return "linux"
    except IOError:
        pass
    return "ambos"
 
 
def log_execution(playbook, hosts, usuario, resultado):
    """Guarda un registro de cada ejecucion para auditoria"""
    entrada = {
        "timestamp": datetime.datetime.now().isoformat(),
        "playbook": playbook,
        "hosts": [h.ip for h in hosts],
        "usuario": usuario,
        "resultado": resultado
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entrada) + "\n")
    except IOError:
        pass
 
 
# GET / - para comprobar que el backend esta vivo
@app.get("/")
def raiz():
    return {"estado": "OK", "mensaje": "Backend Ansible Visual funcionando"}
 
 
# GET /credentials - devuelve las credenciales que haya en el json
# Devuelve los usuarios pero NO las contraseñas al frontend: solo indica si
# estan configuradas (tiene_pass: true/false). Las contraseñas solo viajan
# del frontend al backend cuando el profesor las guarda o ejecuta un playbook,
# nunca en sentido contrario.
@app.get("/credentials")
def obtener_credenciales():
    if os.path.isfile(CREDS_FILE):
        try:
            with open(CREDS_FILE) as f:
                data = json.load(f)
            return {
                "estado": "OK",
                "linux_user": data.get("linux_user", ""),
                "linux_tiene_pass": bool(data.get("linux_pass", "")),
                "win_user": data.get("win_user", ""),
                "win_tiene_pass": bool(data.get("win_pass", ""))
            }
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "estado": "OK",
        "linux_user": "",
        "linux_tiene_pass": False,
        "win_user": "",
        "win_tiene_pass": False
    }
 
 
# POST /credentials - guarda las credenciales que manda el profesor desde la web
# Solo actualiza los campos que llegan rellenos, no machaca los que no vienen.
# Las contraseñas se guardan en texto plano en credentials.json (dentro del
# contenedor). Para mayor seguridad en produccion se podria cifrar con ansible-vault,
# pero para un entorno de aula esto es suficiente.
@app.post("/credentials")
def guardar_credenciales(data: CredencialesGuardar):
    # cargamos lo que ya habia (si existe el fichero)
    actual = {}
    if os.path.isfile(CREDS_FILE):
        try:
            with open(CREDS_FILE) as f:
                actual = json.load(f)
        except (json.JSONDecodeError, IOError):
            actual = {}
 
    # solo actualizamos los campos que han llegado rellenos
    # asi si el profe solo cambia el usuario de Linux, la pass de Windows no se toca
    if data.linux_user is not None:
        actual["linux_user"] = data.linux_user
    if data.linux_pass is not None and data.linux_pass != "":
        actual["linux_pass"] = data.linux_pass
    if data.win_user is not None:
        actual["win_user"] = data.win_user
    if data.win_pass is not None and data.win_pass != "":
        actual["win_pass"] = data.win_pass
 
    # comprobacion basica de usuarios (misma regex que en execute)
    for campo in ("linux_user", "win_user"):
        val = actual.get(campo, "")
        if val and not re.match(r"^[a-zA-Z0-9_\-\.@]+$", val):
            raise HTTPException(400, f"Nombre de usuario no valido en '{campo}'")
 
    # guardamos
    try:
        with open(CREDS_FILE, "w") as f:
            json.dump(actual, f, indent=2)
    except IOError as e:
        raise HTTPException(500, f"No se pudo guardar el fichero de credenciales: {e}")
 
    return {"estado": "OK", "mensaje": "Credenciales guardadas correctamente"}
 
 
# GET /scan - aqui es donde entra nmap
# Buscamos los puertos 22 (SSH, o sea Linux) y 5985 (WinRM, o sea Windows)
# y con eso diferenciamos el SO de cada maquina que encontremos
@app.get("/scan")
def escanear_red(subnet: str = "192.168.1.0/24"):
    if not re.match(r"^[0-9./]+$", subnet):
        return {"estado": "ERROR", "detalle": "Formato de red no valido"}
 
    try:
        resultado = subprocess.run(
            ["/usr/bin/nmap", "-p", "22,5985", "-T4", "--open", "-oG", "-", subnet],
            capture_output=True, text=True, timeout=120
        )
    except subprocess.TimeoutExpired:
        return {"estado": "ERROR", "detalle": "El escaneo ha tardado demasiado"}
 
    equipos = []
    for linea in resultado.stdout.splitlines():
        if "Host:" not in linea or "/open" not in linea:
            continue
 
        ip_match = re.search(r'Host: ([0-9.]+)', linea)
        if not ip_match:
            continue
        ip = ip_match.group(1)
 
        tiene_ssh   = "22/open" in linea
        tiene_winrm = "5985/open" in linea
 
        if tiene_winrm:
            os_name, icon = "Windows", "fab fa-windows"
        elif tiene_ssh:
            os_name, icon = "Linux", "fab fa-linux"
            # a veces nmap pilla el banner de SSH y podemos sacar la distro
            banner = re.search(r'//ssh//(.*?)/', linea)
            if banner:
                b = banner.group(1).lower()
                if "ubuntu" in b:      os_name, icon = "Ubuntu", "fab fa-ubuntu"
                elif "debian" in b:    os_name, icon = "Debian", "fab fa-linux"
                elif "raspbian" in b:  os_name, icon = "Raspberry Pi", "fab fa-raspberry-pi"
                elif "windows" in b:   os_name, icon = "Windows", "fab fa-windows"
        else:
            os_name, icon = "Desconocido", "fas fa-question-circle"
 
        equipos.append({"ip": ip, "os": os_name, "icon": icon})
 
    return {"estado": "OK", "equipos": equipos}
 
 
# GET /playbooks - lista todos los que hay (tanto los que vienen de serie
# como los que haya creado el usuario)
# Ahora incluye el campo os_target para que el frontend sepa a que SO va cada uno
@app.get("/playbooks")
def listar_playbooks():
    playbooks = []
    for tipo, carpeta, editable in [("templates", TEMPLATES_DIR, False),
                                     ("custom", CUSTOM_DIR, True)]:
        if os.path.isdir(carpeta):
            for f in sorted(os.listdir(carpeta)):
                if f.endswith(".yml"):
                    ruta = os.path.join(carpeta, f)
                    playbooks.append({
                        "nombre": f,
                        "tipo": tipo,
                        "editable": editable,
                        "os_target": detectar_os_playbook(ruta)
                    })
    return {"estado": "OK", "playbooks": playbooks}
 
 
# GET /logs - devuelve el historial de ejecuciones para auditoria
@app.get("/logs")
def obtener_logs(limit: int = 50):
    if not os.path.isfile(LOG_FILE):
        return {"estado": "OK", "logs": []}
    try:
        with open(LOG_FILE) as f:
            lineas = f.readlines()
        logs = []
        for linea in lineas[-limit:]:
            try:
                logs.append(json.loads(linea.strip()))
            except json.JSONDecodeError:
                continue
        return {"estado": "OK", "logs": logs}
    except IOError:
        return {"estado": "OK", "logs": []}
 
 
# GET /playbooks/{tipo}/{nombre} - lee el contenido de un playbook concreto
@app.get("/playbooks/{tipo}/{nombre}")
def leer_playbook(tipo: str, nombre: str):
    if tipo not in ("templates", "custom"):
        raise HTTPException(400, "El tipo tiene que ser 'templates' o 'custom'")
    if not nombre_ok(nombre):
        raise HTTPException(400, "Nombre de archivo no valido")
 
    carpeta = TEMPLATES_DIR if tipo == "templates" else CUSTOM_DIR
    ruta = os.path.join(carpeta, nombre)
 
    if not ruta_segura(ruta, carpeta):
        raise HTTPException(403, "Acceso denegado")
    if not os.path.isfile(ruta):
        raise HTTPException(404, "No se encuentra ese playbook")
 
    with open(ruta) as f:
        return {"estado": "OK", "nombre": nombre, "tipo": tipo, "contenido": f.read()}
 
 
# POST /playbooks - para guardar un playbook nuevo hecho por el usuario
@app.post("/playbooks")
def guardar_playbook(data: PlaybookData):
    nombre = data.nombre if data.nombre.endswith(".yml") else data.nombre + ".yml"
 
    if not nombre_ok(nombre):
        raise HTTPException(400, "Nombre no valido. Solo letras, numeros, guiones y _")
 
    # antes de guardar comprobamos que el YAML este bien formado
    try:
        yaml.safe_load(data.contenido)
    except yaml.YAMLError as e:
        raise HTTPException(400, f"El YAML tiene errores: {e}")
 
    ruta = os.path.join(CUSTOM_DIR, nombre)
    if not ruta_segura(ruta, CUSTOM_DIR):
        raise HTTPException(403, "Acceso denegado")
 
    with open(ruta, "w") as f:
        f.write(data.contenido)
 
    return {"estado": "OK", "mensaje": f"Playbook '{nombre}' guardado", "nombre": nombre}
 
 
# POST /execute - la chicha del asunto: ejecutar un playbook en una o varias maquinas
# Lo que hacemos es montar un inventario temporal con las IPs y credenciales que nos
# pasan, lanzar ansible-playbook y mandar la salida por streaming para que en la web
# se vea en tiempo real. Cuando termina, borramos el inventario temporal.
#
# NOTA: si el frontend no manda credenciales explicitas (campos vacios),
# las cogemos del credentials.json como fallback. Asi el profe no tiene que
# escribirlas cada vez si ya las guardo.
@app.post("/execute")
def ejecutar_playbook(data: ExecuteData):
    # primero validamos todo
    if not nombre_ok(data.playbook):
        raise HTTPException(400, "Nombre de playbook no valido")
    if data.tipo not in ("templates", "custom"):
        raise HTTPException(400, "El tipo tiene que ser 'templates' o 'custom'")
    if not data.hosts:
        raise HTTPException(400, "Hace falta al menos una IP")
    for h in data.hosts:
        if not ip_ok(h.ip):
            raise HTTPException(400, f"IP no valida: {h.ip}")
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", data.credenciales.usuario):
        raise HTTPException(400, "Nombre de usuario no valido")
 
    # si la password llega vacia, intentamos usar la guardada en credentials.json
    password_efectiva = data.credenciales.password
    if not password_efectiva and os.path.isfile(CREDS_FILE):
        try:
            with open(CREDS_FILE) as f:
                creds_guardadas = json.load(f)
            # detectamos si los hosts son windows o linux para saber que pass usar
            hay_windows = any("windows" in h.os.lower() for h in data.hosts)
            if hay_windows:
                password_efectiva = creds_guardadas.get("win_pass", "")
            else:
                password_efectiva = creds_guardadas.get("linux_pass", "")
        except (json.JSONDecodeError, IOError):
            pass
 
    if not password_efectiva:
        raise HTTPException(400, "No hay contraseña disponible. Configurala en Credenciales.")
 
    carpeta = TEMPLATES_DIR if data.tipo == "templates" else CUSTOM_DIR
    pb_path = os.path.realpath(os.path.join(carpeta, data.playbook))
 
    if not ruta_segura(pb_path, carpeta):
        raise HTTPException(403, "Acceso denegado")
    if not os.path.isfile(pb_path):
        raise HTTPException(404, "No se encuentra ese playbook")
 
    # montamos el inventario en formato YAML con grupos windows/linux
    # para que los playbooks multi-SO funcionen con hosts: windows / hosts: linux
    inv_data = {"all": {"children": {"windows": {"hosts": {}}, "linux": {"hosts": {}}}}}
    for h in data.hosts:
        if "windows" in h.os.lower():
            inv_data["all"]["children"]["windows"]["hosts"][h.ip] = {
                "ansible_user": data.credenciales.usuario,
                "ansible_password": password_efectiva,
                "ansible_connection": "winrm",
                "ansible_port": 5985,
                "ansible_winrm_scheme": "http",
                "ansible_winrm_transport": "ntlm",
                "ansible_become": False
            }
        else:
            inv_data["all"]["children"]["linux"]["hosts"][h.ip] = {
                "ansible_user": data.credenciales.usuario,
                "ansible_ssh_pass": password_efectiva,
                "ansible_become": True,
                "ansible_become_method": "sudo",
                "ansible_become_pass": password_efectiva
            }
 
    inv_text = yaml.dump(inv_data, default_flow_style=False)
 
    # creamos un archivo temporal para el inventario
    fd, inv_tmp = tempfile.mkstemp(suffix=".yml", prefix="inv_",
                                   dir=ANSIBLE_DIR + "/inventory")
    with os.fdopen(fd, "w") as f:
        f.write(inv_text)
 
    # permisos estrictos: solo root puede leer el inventario temporal
    # (tiene credenciales en texto plano)
    os.chmod(inv_tmp, 0o600)
 
    # montamos el comando de ansible-playbook
    cmd = ["/usr/bin/ansible-playbook", "-i", inv_tmp, pb_path]
    # si hay fichero de vault password, lo usamos
    if os.path.isfile(VAULT_PASS):
        cmd.extend(["--vault-password-file", VAULT_PASS])
 
    # la salida la mandamos en streaming, asi el usuario ve lo que va pasando
    # sin tener que esperar a que acabe todo el playbook
    def generar_salida():
        resultado = "UNKNOWN"
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=ANSIBLE_DIR
            )
            for linea in iter(proc.stdout.readline, ""):
                yield linea
            proc.wait()
            if proc.returncode == 0:
                resultado = "OK"
                yield "\n--- RESULTADO: OK ---\n"
            else:
                resultado = "ERROR (" + str(proc.returncode) + ")"
                yield "\n--- RESULTADO: ERROR (código " + str(proc.returncode) + ") ---\n"
        except Exception as e:
            resultado = "EXCEPTION"
            yield "\nError: " + str(e) + "\n"
        finally:
            # limpiamos el inventario temporal para no dejar credenciales tiradas
            if os.path.exists(inv_tmp):
                os.unlink(inv_tmp)
            # registramos la ejecucion en el log de auditoria
            log_execution(data.playbook, data.hosts, data.credenciales.usuario, resultado)
 
    return StreamingResponse(generar_salida(), media_type="text/plain")
 
