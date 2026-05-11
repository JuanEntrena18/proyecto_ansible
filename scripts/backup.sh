#!/bin/sh

# Configuración
BACKUP_DIR="/backups"
DATA_SOURCE="/data"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "Starting backup: ${DATE}"

# Crear el archivo comprimido con los tres orígenes definidos en el docker-compose
tar -czf ${BACKUP_DIR}/backup_${DATE}.tar.gz \
    ${DATA_SOURCE}/playbooks \
    ${DATA_SOURCE}/logs \
    ${DATA_SOURCE}/credentials.json

# Rotación: Borrar archivos con más de 30 días
find ${BACKUP_DIR} -name "backup_*.tar.gz" -mtime +${RETENTION_DAYS} -exec rm {} \;

echo "Backup completed successfully."
