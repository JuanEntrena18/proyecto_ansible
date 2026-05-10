#!/bin/sh
# scripts/backup.sh
# Se ejecuta dentro del contenedor Alpine cada dia a las 02:00
# y tambien al arrancar el contenedor por primera vez.
#
# Que guarda:
#   /data/playbooks/  -> playbooks custom creados por los profesores
#   /data/logs/       -> historial de ejecuciones de ansible
#   /data/credentials.json -> credenciales de los equipos de aula
#
# Donde lo guarda:
#   /backups/YYYY-MM-DD_HH-MM.tar.gz
#
# Retencion: 30 dias (borra los mas antiguos automaticamente)

set -e

DESTINO="/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
ARCHIVO="$DESTINO/ansible-visual_$TIMESTAMP.tar.gz"
DIAS_RETENCION=30

mkdir -p "$DESTINO"

echo "[backup] $(date '+%Y-%m-%d %H:%M:%S') - Iniciando backup..."

# Creamos el .tar.gz con todo lo que hay en /data
# --ignore-failed-read por si algun archivo esta en uso en ese momento
tar czf "$ARCHIVO" \
    --ignore-failed-read \
    -C / \
    data/playbooks \
    data/logs \
    data/credentials.json \
    2>/dev/null || true

TAMANIO=$(du -sh "$ARCHIVO" 2>/dev/null | cut -f1)
echo "[backup] $(date '+%Y-%m-%d %H:%M:%S') - Backup creado: $ARCHIVO ($TAMANIO)"

# Borramos backups con mas de DIAS_RETENCION dias
BORRADOS=$(find "$DESTINO" -name "ansible-visual_*.tar.gz" -mtime +$DIAS_RETENCION -print)
if [ -n "$BORRADOS" ]; then
    echo "[backup] Limpiando backups antiguos (>${DIAS_RETENCION} dias):"
    echo "$BORRADOS" | while read f; do
        echo "  Borrando: $f"
        rm -f "$f"
    done
else
    echo "[backup] No hay backups antiguos que limpiar."
fi

# Contamos cuantos backups tenemos
TOTAL=$(find "$DESTINO" -name "ansible-visual_*.tar.gz" | wc -l)
echo "[backup] $(date '+%Y-%m-%d %H:%M:%S') - Backups disponibles: $TOTAL"
echo "[backup] Fin."
