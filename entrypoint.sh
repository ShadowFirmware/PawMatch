#!/bin/bash
set -e

echo "⏳ Esperando a la base de datos..."
until python -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PawMatch.settings')
import django
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "  Base de datos no disponible, reintentando en 3s..."
    sleep 3
done

echo "✅ Base de datos lista"
echo "🔄 Ejecutando migraciones..."
python manage.py migrate --noinput

echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "🚀 Iniciando Daphne (ASGI) en puerto ${PORT:-8000}..."
exec daphne -b 0.0.0.0 -p "${PORT:-8000}" PawMatch.asgi:application
