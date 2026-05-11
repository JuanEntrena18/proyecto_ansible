# main.py
# Este es el backend del proyecto. Basicamente es una API hecha con FastAPI
# que se encarga de escanear la red local con nmap, listar los playbooks
# que tenemos guardados y ejecutarlos contra las maquinas que el usuario
# elija desde la interfaz web. Para Linux usa SSH y para Windows WinRM.

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
import subprocess, re, os, yaml, tempfile, json, secrets

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

# --- JWT y autenticacion ---
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

USERS = {
    "admin":    {"password": hash_password("admin"), "rol": "admin"},
    "operador": {"password": hash_password("operador"), "rol": "operador"},
}

# --- Cifrado de credentials.json ---
fernet = None
CREDS_KEY_FILE = os.path.join(ANSIBLE_DIR, ".credentials_key")

def init_crypto():
    global fernet
    key = os.environ.get("CREDENTIALS_KEY")
    if key:
        fernet = Fernet(key.encode() if not key.endswith("=") else key)
    elif os.path.isfile(CREDS_KEY_FILE):
        with open(CREDS_KEY_FILE) as f:
            fernet = Fernet(f.read().strip().encode())
    else:
        k = Fernet.generate_key()
        with open(CREDS_KEY_FILE, "wb") as f:
            f.write(k)
        fernet = Fernet(k)

init_crypto()

def load_creds():
    if not os.path.isfile(CREDS_FILE):
        return {}
    try:
        with open(CREDS_FILE) as f:
            content = f.read().strip()
        if not content:
            return {}
        if fernet:
            try:
                return json.loads(fernet.decrypt(content.encode()).decode())
            except Exception:
                pass
        return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return {}

def save_creds(data):
    text = json.dumps(data, indent=2)
    if fernet:
        text = fernet.encrypt(text.encode()).decode()
    with open(CREDS_FILE, "w") as f:
        f.write(text)

# --- Funciones de autenticacion ---

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)):
    if auth is None:
        raise HTTPException(401, "Token requerido")
    try:
        payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("rol")
        if not username or not role:
            raise HTTPException(401, "Token invalido")
        return {"username": username, "rol": role}
    except JWTError:
        raise HTTPException(401, "Token invalido o expirado")

async def require_admin(current_user=Depends(get_current_user)):
    if current_user["rol"] != "admin":
        raise HTTPException(403, "Se requiere rol de administrador")
    return current_user


# --- Modelos de datos para las peticiones ---

class LoginRequest(BaseModel):
    username: str
    password: str

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

class CredencialesGuardar(BaseModel):
    linux_user: Optional[str] = None
    linux_pass: Optional[str] = None
    win_user: Optional[str] = None
    win_pass: Optional[str] = None


# --- Funciones de validacion ---

def nombre_ok(nombre):
    return bool(nombre and ".." not in nombre and "/" not in nombre
                and "\\" not in nombre and re.match(r"^[a-zA-Z0-9_\-]+\.yml$", nombre))

def ip_ok(ip):
    return bool(re.match(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$", ip))

def ruta_segura(ruta, directorio_base):
    return os.path.realpath(ruta).startswith(os.path.realpath(directorio_base))

def detectar_os_playbook(ruta):
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
    entrada = {
        "timestamp": datetime.now().isoformat(),
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


# --- Endpoints de autenticacion ---

@app.post("/login")
def login(data: LoginRequest):
    user = USERS.get(data.username)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Usuario o contrasena incorrectos")
    token = create_access_token({"sub": data.username, "rol": user["rol"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": user["rol"],
        "username": data.username
    }

@app.get("/me")
def me(current_user=Depends(get_current_user)):
    return current_user


# GET / - para comprobar que el backend esta vivo
@app.get("/")
def raiz():
    return {"estado": "OK", "mensaje": "Backend Ansible Visual funcionando"}


# GET /credentials - devuelve las credenciales que haya en el json
# Solo accesible para admin
@app.get("/credentials")
def obtener_credenciales(current_user=Depends(require_admin)):
    data = load_creds()
    return {
        "estado": "OK",
        "linux_user": data.get("linux_user", ""),
        "linux_tiene_pass": bool(data.get("linux_pass", "")),
        "win_user": data.get("win_user", ""),
        "win_tiene_pass": bool(data.get("win_pass", ""))
    }


# POST /credentials - guarda las credenciales que manda el profesor desde la web
# Solo accesible para admin. Se guardan cifradas en disco.
@app.post("/credentials")
def guardar_credenciales(data: CredencialesGuardar, current_user=Depends(require_admin)):
    actual = load_creds()
    if data.linux_user is not None:
        actual["linux_user"] = data.linux_user
    if data.linux_pass is not None and data.linux_pass != "":
        actual["linux_pass"] = data.linux_pass
    if data.win_user is not None:
        actual["win_user"] = data.win_user
    if data.win_pass is not None and data.win_pass != "":
        actual["win_pass"] = data.win_pass
    for campo in ("linux_user", "win_user"):
        val = actual.get(campo, "")
        if val and not re.match(r"^[a-zA-Z0-9_\-\.@]+$", val):
            raise HTTPException(400, f"Nombre de usuario no valido en '{campo}'")
    try:
        save_creds(actual)
    except IOError as e:
        raise HTTPException(500, f"No se pudo guardar: {e}")
    return {"estado": "OK", "mensaje": "Credenciales guardadas correctamente"}


# GET /scan - escanea la red con nmap
@app.get("/scan")
def escanear_red(subnet: str = "192.168.1.0/24", current_user=Depends(get_current_user)):
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


# GET /playbooks - lista todos los playbooks disponibles
@app.get("/playbooks")
def listar_playbooks(current_user=Depends(get_current_user)):
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


# GET /logs - historial de ejecuciones (solo admin)
@app.get("/logs")
def obtener_logs(limit: int = 50, current_user=Depends(require_admin)):
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


# GET /playbooks/{tipo}/{nombre} - lee el contenido de un playbook
@app.get("/playbooks/{tipo}/{nombre}")
def leer_playbook(tipo: str, nombre: str, current_user=Depends(get_current_user)):
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


# POST /playbooks - guarda un playbook nuevo (solo admin)
@app.post("/playbooks")
def guardar_playbook(data: PlaybookData, current_user=Depends(require_admin)):
    nombre = data.nombre if data.nombre.endswith(".yml") else data.nombre + ".yml"
    if not nombre_ok(nombre):
        raise HTTPException(400, "Nombre no valido. Solo letras, numeros, guiones y _")
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


# POST /execute - ejecuta un playbook (solo admin)
# Si el frontend no manda password, se coge la guardada en credentials.json
@app.post("/execute")
def ejecutar_playbook(data: ExecuteData, current_user=Depends(require_admin)):
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

    password_efectiva = data.credenciales.password
    if not password_efectiva:
        creds_guardadas = load_creds()
        hay_windows = any("windows" in h.os.lower() for h in data.hosts)
        if hay_windows:
            password_efectiva = creds_guardadas.get("win_pass", "")
        else:
            password_efectiva = creds_guardadas.get("linux_pass", "")

    if not password_efectiva:
        raise HTTPException(400, "No hay contrasena disponible. Configurala en Credenciales.")

    carpeta = TEMPLATES_DIR if data.tipo == "templates" else CUSTOM_DIR
    pb_path = os.path.realpath(os.path.join(carpeta, data.playbook))
    if not ruta_segura(pb_path, carpeta):
        raise HTTPException(403, "Acceso denegado")
    if not os.path.isfile(pb_path):
        raise HTTPException(404, "No se encuentra ese playbook")

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

    fd, inv_tmp = tempfile.mkstemp(suffix=".yml", prefix="inv_",
                                   dir=ANSIBLE_DIR + "/inventory")
    with os.fdopen(fd, "w") as f:
        f.write(inv_text)
    os.chmod(inv_tmp, 0o600)

    cmd = ["/usr/bin/ansible-playbook", "-i", inv_tmp, pb_path]
    if os.path.isfile(VAULT_PASS):
        cmd.extend(["--vault-password-file", VAULT_PASS])

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
                yield "\n--- RESULTADO: ERROR (codigo " + str(proc.returncode) + ") ---\n"
        except Exception as e:
            resultado = "EXCEPTION"
            yield "\nError: " + str(e) + "\n"
        finally:
            if os.path.exists(inv_tmp):
                os.unlink(inv_tmp)
            log_execution(data.playbook, data.hosts, data.credenciales.usuario, resultado)

    return StreamingResponse(generar_salida(), media_type="text/plain")
