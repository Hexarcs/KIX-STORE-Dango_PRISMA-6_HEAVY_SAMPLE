#!/bin/bash

set -e

echo "=============================================="
echo "  MONTANDO KIX STORE (ALLAUTH LOCAL + GOOGLE)"
echo "=============================================="

LOJA_DIR="."

# ================================================================
# 0. CRIA O ARQUIVO .ENV
# ================================================================

echo "[0/3] Escrevendo o arquivo .env..."

cat << 'EOF' > "$LOJA_DIR/.env"
COINAPI_KEY=suaapikeycoinsaqui
LNBITS_API_KEY=suaapikeylnbitsaqui
LNBITS_URL=https://seuendpointlnbitsaqui/api/v1/payments
SECRET_KEY=django-insecure-suachavesecretadeaprendizadoaqui
DEBUG=False
ALLOWED_HOSTS=*
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
WHATSAPP_ATIVO=false
WHATSAPP_NUMERO=
WHATSAPP_MENSAGEM_PADRAO=Olá
EOF

# ================================================================
# 1. CRIA O entrypoint.sh
# ================================================================

echo "[1/3] Criando entrypoint.sh..."

cat << 'EOF' > entrypoint.sh
#!/bin/sh

python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    from django.conf import settings
    import sys

    mod = sys.modules[settings.SETTINGS_MODULE]
    settings_file = mod.__file__

    with open(settings_file, 'r') as f:
        content = f.read()

    if 'SOCIALACCOUNT_ONLY' not in content:
        with open(settings_file, 'a') as f:
            f.write('''

# --- CONFIGURACOES DE PROXY E CSRF IRRESTRITAS ---
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*']
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

# --- AJUSTES DO ALLAUTH PARA CADASTRO/LOGIN LOCAL ---
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ALLOW_REGISTRATION = True
SOCIALACCOUNT_ONLY = False
''')
        print(f'Configuracoes do Allauth injetadas em: {settings_file}')
    else:
        print('Configuracoes do Allauth ja presentes.')

except Exception as e:
    print(f'Erro ao injetar configuracoes: {e}')
"

python manage.py makemigrations
python manage.py migrate

# Coleta os arquivos estáticos (whitenoise serve /static/ com DEBUG=False)
python manage.py collectstatic --noinput

# Garante superusuário ativo
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'zeloko@example.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'Industria12!')

user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True})
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.save()
"

python manage.py runserver 0.0.0.0:8000
EOF

# ================================================================
# 2. CRIA O docker-compose.yml
# ================================================================

echo "[2/3] Criando docker-compose.yml..."

cat << 'EOF' > docker-compose.yml
services:
  web:
    image: zeloko/supermercado-kix:latest
    container_name: Store
    ports:
      - "8006:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./media:/app/media
      - ./entrypoint.sh:/app/entrypoint.sh
    environment:
      - DEBUG=0
      - DJANGO_SUPERUSER_USERNAME=admin
      - DJANGO_SUPERUSER_EMAIL=zeloko
      - DJANGO_SUPERUSER_PASSWORD=Industria12!
    command: /bin/sh /app/entrypoint.sh
    restart: unless-stopped
EOF

# ================================================================
# 3. PERMISSÃO E RECRIAÇÃO DO CONTAINER
# ================================================================

echo "[3/3] Aplicando permissões..."
chmod +x entrypoint.sh

echo "[INFO] Limpando containers antigos..."
docker compose down -v || true

echo "[INFO] Subindo o novo container..."
docker compose up -d

echo ""
echo "=============================================="
echo "  KIX STORE PRONTO (LOGIN LOCAL + GOOGLE)"
echo "=============================================="
