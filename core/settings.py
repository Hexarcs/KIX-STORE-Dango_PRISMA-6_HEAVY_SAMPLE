import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Puxa a chave do .env; se não achar, usa um fallback temporário
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-local-key')

# Converte o valor de DEBUG do .env para Booleano
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Configurações do Telegram (notificações de contato do rodapé)
# Prioridade: .env; se vazio, usa ConfiguracaoTelegram (painel admin).
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
TELEGRAM_TIMEOUT = 10

# Configurações do botão flutuante de WhatsApp (Click-to-Chat)
# Prioridade: painel admin (ConfiguracaoWhatsApp); o .env é fallback quando o
# campo correspondente estiver vazio no banco.
WHATSAPP_ATIVO = os.getenv('WHATSAPP_ATIVO', '')
WHATSAPP_NUMERO = os.getenv('WHATSAPP_NUMERO', '')
WHATSAPP_MENSAGEM_PADRAO = os.getenv('WHATSAPP_MENSAGEM_PADRAO', 'Olá')

# ⚡ OBRIGATÓRIO PARA HTTPS: Permite requisições POST (como o add do carrinho) vindas do seu domínio
CSRF_TRUSTED_ORIGINS = [
    'https://engine-99.libertariamemes.com.br',
    'https://supermercado.hexarcs.com.br',
     'https://supermercado.hexarcs.com',
]


# Application definition

INSTALLED_APPS = [
    'core',  # 🌟 Adicione isso aqui para o Django rastrear seus modelos!
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Módulos obrigatórios para o Allauth funcionar
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 🌟 ADICIONE ESTA LINHA AQUI PARA ATIVAR O GOOGLE:
    'allauth.socialaccount.providers.google',
]

# Configuração do ID do site (obrigatório para o django.contrib.sites)
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # 🌟 ADICIONE ESTA LINHA EXATAMENTE AQUI:
    'allauth.account.middleware.AccountMiddleware',
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 🌟 Modifique ESTA linha abaixo:
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Essencial para o Allauth injetar dados do usuário na tela
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ADICIONE ESTA LINHA AQUI:
                'core.context_processors.btc_context',
                'core.context_processors.site_config_processor',
                'core.context_processors.cards_processor',  # <--- Este aqui
                'core.context_processors.telegram_config_processor',
                'core.context_processors.rodape_config_processor',
                'core.context_processors.whatsapp_config_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
########-----------------------------------------------##############
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

# 1. Rota de URL para arquivos estáticos
STATIC_URL = '/static/'

# 2. Onde o Django vai buscar os estáticos em modo Desenvolvimento (Resolve o script.js)
STATICFILES_DIRS = [
    BASE_DIR / "core" / "static",
]

# 3. Onde o Django vai agrupar tudo para produção ao rodar o collectstatic
STATIC_ROOT = BASE_DIR / "staticfiles"


# --- Autenticação e resto das suas configurações que já estavam aí ---

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Redirecionamentos pós-login/logout
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Customizações do Allauth (Sintaxe Estrita Atualizada)
#ACCOUNT_LOGIN_METHODS = {'email'}
#ACCOUNT_SIGNUP_FIELDS = ['email*']  # O '*' resolve o erro crítico de e-mail obrigatório
#ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
#ACCOUNT_SESSION_REMEMBER = True

# --- CONFIGURAÇÕES DO ALLAUTH (LOGIN LOCAL + GOOGLE) ---
# Permite entrar tanto digitando e-mail quanto username
ACCOUNT_LOGIN_METHODS = {'email', 'username'}

# Exige o campo de e-mail no cadastro local
#ACCOUNT_SIGNUP_FIELDS = ['email*']

# Desativa o bloqueio de conta pendente de confirmação de e-mail
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Libera o cadastro local por formulário tradicional e mantém o login social
ACCOUNT_ALLOW_REGISTRATION = True
SOCIALACCOUNT_ONLY = False

# Mantém a sessão salva
ACCOUNT_SESSION_REMEMBER = True

# Envia e-mails de desenvolvimento para o console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

import os

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
########---------------------------------------------------##############


# =========================================================================
# LOGGING: faz os logs da aplicação (ex.: falhas no Telegram) aparecerem
# =========================================================================
LOG_DIR = BASE_DIR / "logs"

# O handler de arquivo só é ativado se o diretório for gravável pelo usuário
# atual. Assim, uma permissão de escrita ausente não derruba a aplicação nem
# polui o console com erros de logging.
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    _arquivo_log_ok = os.access(LOG_DIR, os.W_OK)
except OSError:
    _arquivo_log_ok = False

_file_handlers = ["console"]
if _arquivo_log_ok:
    _file_handlers.append("file")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
            # Abre o arquivo só no primeiro log (não derruba o startup se não puder escrever)
            "delay": True,
        },
    },
    "root": {"handlers": _file_handlers, "level": "INFO"},
    "loggers": {
        "core": {"handlers": _file_handlers, "level": "DEBUG", "propagate": False},
    },
}


