#!/bin/sh

# ==========================================
# Configuración del Backup Visual/Ansible
# ==========================================
BACKUP_DIR="/backups"
DATA_SOURCE="/data"
DATE=$(date +%Y%m%d_%H%M%S)
LOCAL_RETENTION_DAYS=7

# Configuración destino Windows 11
WIN_USER="profesor_it"
WIN_IP="192.168.1.45"
WIN_DEST="C:/Backups_VisualAnsible/"

echo "========================================="
echo " Iniciando copia de seguridad: ${DATE}"
echo "========================================="

# 1. Empaquetado y compresión de datos vitales
tar -czf ${BACKUP_DIR}/backup_${DATE}.tar.gz \
    ${DATA_SOURCE}/playbooks \
    ${DATA_SOURCE}/logs \
    ${DATA_SOURCE}/credentials.json \
    ${DATA_SOURCE}/usuarios.db \
    ${DATA_SOURCE}/inventory.json

echo "Copia local empaquetada correctamente en ${BACKUP_DIR}."

# 2. Rotación Local (Ahorro de disco en el servidor Ubuntu)
echo "Limpiando backups locales antiguos (+${LOCAL_RETENTION_DAYS} días)..."
find ${BACKUP_DIR} -name "backup_*.tar.gz" -mtime +${LOCAL_RETENTION_DAYS} -exec rm {} \;

# 3. Sincronización Externa hacia Windows 11 (Vía SCP)
# Requiere que el servicio "OpenSSH Server" esté habilitado en Windows 11
echo "Sincronizando con el equipo de administración (192.168.1.45)..."
scp -o StrictHostKeyChecking=no ${BACKUP_DIR}/backup_${DATE}.tar.gz ${WIN_USER}@${WIN_IP}:${WIN_DEST}

echo "========================================="
echo " Backup completado y exportado con éxito."
echo "========================================="
