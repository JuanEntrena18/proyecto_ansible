FROM python:3.12-slim

# paquetes del sistema que necesitamos: nmap para escanear la red,
# sshpass para que ansible pueda enviar contraseñas por SSH y
# openssh-client para la propia conexion SSH
RUN apt-get update && \
    apt-get install -y --no-install-recommends nmap sshpass openssh-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ansible-visual/api

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir ansible-core && \
    ansible-galaxy collection install --force -p /usr/share/ansible/collections ansible.windows && \
    ansible-galaxy collection install --force -p /usr/share/ansible/collections chocolatey.chocolatey && \
    ansible-galaxy collection install --force -p /usr/share/ansible/collections community.general && \
    ansible-galaxy collection install --force -p /usr/share/ansible/collections community.windows

# pip mete los binarios en /usr/local/bin/ pero en main.py los
# llamamos con /usr/bin/, asi que creamos enlaces simbolicos
RUN ln -sf /usr/local/bin/ansible-playbook /usr/bin/ansible-playbook && \
    ln -sf /usr/local/bin/ansible-config /usr/bin/ansible-config && \
    ln -sf /usr/local/bin/ansible /usr/bin/ansible

COPY main.py .

EXPOSE 8000

CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]
