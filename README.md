# KIX Store — Deploy Automatizado

Este projeto utiliza o `deploy.sh` como **script oficial de implantação** da KIX Store.

O script prepara automaticamente a instância Django, cria o `.env`, gera o `entrypoint.sh`, configura o `docker-compose.yml`, aplica as configurações necessárias do Django/Allauth, executa as migrações, garante a existência do superusuário e sobe o container Docker.

A aplicação utiliza:

* Django
* Django Allauth
* Login local por usuário/e-mail
* Login social via Google
* Docker Compose
* Volumes persistentes para `data` e `media`
* Banco de dados/migrações gerenciados pelo Django
* Configuração para funcionamento atrás de proxy reverso

---

## 1. Estrutura esperada

O deploy deve ser executado **dentro do diretório da instância da loja**.

A estrutura ficará semelhante a:

```text
Hexarcs_loja/
├── deploy.sh
├── entrypoint.sh
├── docker-compose.yml
├── .env
├── data/
└── media/
```

O `deploy.sh` é o ponto de entrada oficial da implantação.

---

# 2. Criar o `deploy.sh`

Crie o arquivo:

```bash
nano deploy.sh
```

Cole o script oficial abaixo:

```bash
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

cat > "$LOJA_DIR/.env" <<'KIX_ENV_FILE'
COINAPI_KEY=suaapikeycoinsaqui
LNBITS_API_KEY=suaapikeylnbitsaqui
LNBITS_URL=https://seuendpointlnbitsaqui/api/v1/payments
SECRET_KEY=django-insecure-suachavesecretadeaprendizadoaqui
DEBUG=False
ALLOWED_HOSTS=*
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
KIX_ENV_FILE

echo "[OK] .env criado."

# ================================================================
# 1. CRIA O entrypoint.sh
# ================================================================

echo "[1/3] Criando entrypoint.sh..."

cat > entrypoint.sh <<'KIX_ENTRYPOINT_FILE'
#!/bin/sh

set -e

echo "=============================================="
echo "  KIX STORE - ENTRYPOINT"
echo "=============================================="

# ================================================================
# 1. APLICA CONFIGURACOES NO SETTINGS.PY
# ================================================================

echo "[1/4] Aplicando configuracoes do Django..."

python -c "
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.conf import settings

settings_module = settings.SETTINGS_MODULE
mod = sys.modules[settings_module]
settings_file = mod.__file__

print('[INFO] SETTINGS_MODULE:', settings_module)
print('[INFO] settings.py:', settings_file)

with open(settings_file, 'r') as f:
    content = f.read()

# ================================================================
# MARCADORES DO BLOCO KIX
# ================================================================

start_marker = '# KIX DEPLOY CONFIG - START'
end_marker = '# KIX DEPLOY CONFIG - END'

# ================================================================
# CONFIGURACAO OFICIAL KIX
# ================================================================

kix_config = '''
# ================================================================
# KIX DEPLOY CONFIG - START
# ================================================================

# --- CONFIGURACOES DE HOST / PROXY ---
ALLOWED_HOSTS = ['*']

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- CONFIGURACOES CSRF ---
CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*']
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

# --- CONFIGURACOES DO ALLAUTH ---
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ALLOW_REGISTRATION = True
SOCIALACCOUNT_ONLY = False

# ================================================================
# KIX DEPLOY CONFIG - END
# ================================================================
'''

# ================================================================
# REMOVE QUALQUER BLOCO KIX ANTERIOR
# ================================================================

start_pos = content.find(start_marker)

if start_pos != -1:

    end_pos = content.find(end_marker, start_pos)

    if end_pos != -1:

        end_pos += len(end_marker)

        content = (
            content[:start_pos].rstrip()
            + '\\n\\n'
            + content[end_pos:].lstrip()
        )

        print('[INFO] Bloco KIX anterior removido.')

    else:

        print('[WARN] Inicio do bloco KIX encontrado, mas final nao.')
        print('[WARN] Nenhuma alteracao parcial sera removida.')

# ================================================================
# ADICIONA O BLOCO OFICIAL NOVAMENTE
# ================================================================

content = content.rstrip()
content += '\\n\\n' + kix_config.strip() + '\\n'

with open(settings_file, 'w') as f:
    f.write(content)

print('[OK] Configuracoes KIX aplicadas.')

# ================================================================
# VALIDACAO
# ================================================================

with open(settings_file, 'r') as f:
    final_content = f.read()

required = [
    'ALLOWED_HOSTS',
    'CSRF_TRUSTED_ORIGINS',
    'USE_X_FORWARDED_HOST',
    'SECURE_PROXY_SSL_HEADER',
    'CSRF_COOKIE_SECURE',
    'CSRF_COOKIE_HTTPONLY',
    'ACCOUNT_AUTHENTICATION_METHOD',
    'ACCOUNT_EMAIL_REQUIRED',
    'ACCOUNT_EMAIL_VERIFICATION',
    'ACCOUNT_ALLOW_REGISTRATION',
    'SOCIALACCOUNT_ONLY'
]

missing = [item for item in required if item not in final_content]

if missing:

    print('[ERRO] Configuracoes ausentes:')

    for item in missing:
        print('  -', item)

    raise SystemExit(1)

print('[OK] Todas as configuracoes KIX foram verificadas.')
"

# ================================================================
# 2. MIGRATIONS
# ================================================================

echo "[2/4] Executando makemigrations..."

python manage.py makemigrations

echo "[2/4] Executando migrate..."

python manage.py migrate

python manage.py collectstatic --noinput

# ================================================================
# 3. GARANTE SUPERUSUARIO
# ================================================================

echo "[3/4] Garantindo superusuario..."

python -c "
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'zeloko@example.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'Industria12!')

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'email': email,
        'is_staff': True,
        'is_superuser': True
    }
)

user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.save()

if created:
    print('[OK] Superusuario criado:', username)
else:
    print('[OK] Superusuario atualizado:', username)
"

# ================================================================
# 4. INICIA DJANGO
# ================================================================

echo "[4/4] Iniciando Django..."

echo "=============================================="
echo "  KIX STORE PRONTO"
echo "  ALLAUTH LOCAL + GOOGLE"
echo "=============================================="

exec python manage.py runserver 0.0.0.0:8000

KIX_ENTRYPOINT_FILE

echo "[OK] entrypoint.sh criado."

# ================================================================
# 2. CRIA O docker-compose.yml
# ================================================================

echo "[2/3] Criando docker-compose.yml..."

cat > docker-compose.yml <<'KIX_COMPOSE_FILE'
services:
  web:
    image: zeloko/supermercado-kix:latest
    container_name: Store_00

    ports:
      - "8006:8000"

    env_file:
      - .env

    volumes:
      - ./data:/app/data
      - ./media:/app/media
      - ./entrypoint.sh:/app/entrypoint.sh

    environment:
      - DEBUG=1
      - DJANGO_SUPERUSER_USERNAME=admin
      - DJANGO_SUPERUSER_EMAIL=zeloko
      - DJANGO_SUPERUSER_PASSWORD=Industria12!

    command: /bin/sh /app/entrypoint.sh

    restart: unless-stopped
KIX_COMPOSE_FILE

echo "[OK] docker-compose.yml criado."

# ================================================================
# 3. VALIDACAO DOS ARQUIVOS
# ================================================================

echo "[3/3] Validando arquivos..."

if [ ! -s .env ]; then
    echo "[ERRO] .env nao foi criado corretamente."
    exit 1
fi

if [ ! -s entrypoint.sh ]; then
    echo "[ERRO] entrypoint.sh nao foi criado corretamente."
    exit 1
fi

if [ ! -s docker-compose.yml ]; then
    echo "[ERRO] docker-compose.yml nao foi criado corretamente."
    exit 1
fi

if ! grep -q "KIX STORE - ENTRYPOINT" entrypoint.sh; then
    echo "[ERRO] entrypoint.sh parece estar incompleto."
    exit 1
fi

if ! grep -q "container_name: Store_00" docker-compose.yml; then
    echo "[ERRO] docker-compose.yml parece estar incompleto."
    exit 1
fi

echo "[OK] Todos os arquivos foram criados corretamente."

# ================================================================
# 4. PERMISSOES
# ================================================================

chmod +x entrypoint.sh

# ================================================================
# 5. RECRIA O CONTAINER
# ================================================================

echo "[INFO] Limpando containers antigos..."

docker compose down -v || true

echo "[INFO] Subindo o novo container..."

docker compose up -d

# ================================================================
# FINAL
# ================================================================

echo ""
echo "=============================================="
echo "  KIX STORE PRONTO"
echo "=============================================="
echo ""
echo "Container: Store_00"
echo "Porta:     8006"
echo ""
echo "Para acompanhar os logs:"
echo "docker compose logs -f"
echo ""
```

Salve com:

```text
Ctrl + O
Enter
Ctrl + X
```

---

# 3. Dar permissão de execução

Depois de criar o script:

```bash
chmod +x deploy.sh
```

---

# 4. Executar o deploy

Execute:

```bash
./deploy.sh
```

O script realizará automaticamente as etapas abaixo.

### Etapa 0 — `.env`

O script cria o arquivo:

```text
.env
```

com as variáveis utilizadas pela aplicação:

```text
COINAPI_KEY
LNBITS_API_KEY
LNBITS_URL
SECRET_KEY
DEBUG
ALLOWED_HOSTS
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

As credenciais mostradas no script são apenas placeholders.

Em uma instalação real, substitua os valores antes de colocar a aplicação em produção.

---

# 5. Criação automática do `entrypoint.sh`

O `deploy.sh` cria um segundo script chamado:

```text
entrypoint.sh
```

Esse arquivo é executado **dentro do container**.

Ele é responsável por preparar a aplicação antes de iniciar o servidor Django.

A sequência é:

```text
Container iniciado
       │
       ▼
entrypoint.sh
       │
       ├── Ajusta configurações Django
       │
       ├── Configura Allauth
       │
       ├── makemigrations
       │
       ├── migrate
       │
       ├── Cria/atualiza superusuário
       │
       └── Inicia Django
```

---

# 6. Configuração do Django Allauth

O `entrypoint.sh` verifica se:

```python
SOCIALACCOUNT_ONLY
```

já está presente nas configurações do Django.

Caso não esteja, ele injeta automaticamente as configurações necessárias para permitir:

* autenticação local;
* autenticação por usuário/e-mail;
* cadastro de usuários;
* login social;
* integração com Google;
* funcionamento atrás de proxy reverso.

As configurações adicionadas são:

```python
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ALLOW_REGISTRATION = True
SOCIALACCOUNT_ONLY = False
```

Isso significa que o sistema **não fica limitado ao login do Google**.

O usuário também pode utilizar o sistema tradicional de autenticação.

---

# 7. Configurações de proxy reverso

O script também adiciona:

```python
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

Essas opções são importantes quando a aplicação Django está atrás de um proxy reverso, como Nginx, que termina a conexão HTTPS antes de encaminhar a requisição para o container.

Nesse cenário, o Django precisa conseguir interpretar corretamente informações como:

```text
Cliente
   │
   │ HTTPS
   ▼
Nginx / Proxy
   │
   │ HTTP interno
   ▼
Docker
   │
   ▼
Django
```

---

# 8. ⚠️ Atenção às configurações de CSRF

O script atualmente utiliza:

```python
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*']
```

Essa configuração é **extremamente permissiva**.

Ela pode ser conveniente durante desenvolvimento, testes ou determinadas configurações de proxy, mas **não deve ser considerada uma configuração segura de produção**.

## `ALLOWED_HOSTS = ['*']`

Essa configuração aceita requisições cujo `Host` pode ser praticamente qualquer domínio.

Em produção, o ideal é especificar somente os domínios realmente utilizados:

```python
ALLOWED_HOSTS = [
    'loja.exemplo.com',
    'www.loja.exemplo.com',
]
```

Isso reduz a superfície de ataque relacionada a hosts inesperados e configurações incorretas de proxy.

---

## `CSRF_TRUSTED_ORIGINS` irrestrito

A configuração:

```python
CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*']
```

é ainda mais importante de observar.

O mecanismo CSRF do Django existe para impedir que uma página externa consiga induzir o navegador de um usuário autenticado a realizar determinadas requisições em seu nome.

Ao confiar genericamente em praticamente qualquer origem HTTP/HTTPS, você perde uma parte importante dessa proteção baseada na origem.

Em produção, prefira declarar explicitamente as origens autorizadas:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://loja.exemplo.com',
]
```

Se existirem vários domínios legítimos:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://loja.exemplo.com',
    'https://www.loja.exemplo.com',
]
```

**Não confunda `CSRF_TRUSTED_ORIGINS` com uma lista de domínios que simplesmente podem acessar o site.** Ela define origens consideradas confiáveis para determinadas verificações CSRF.

---

# 9. Cookies CSRF

O script também utiliza:

```python
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
```

Essas opções são permissivas.

Em uma aplicação que opera exclusivamente em HTTPS, normalmente é preferível utilizar:

```python
CSRF_COOKIE_SECURE = True
```

O `HTTPONLY` possui uma consideração diferente: mantê-lo `False` permite que JavaScript acesse o cookie CSRF quando necessário por determinada arquitetura frontend. Portanto, essa configuração deve ser definida de acordo com a forma como a aplicação realmente envia o token CSRF.

O importante é **não copiar essas configurações de desenvolvimento para produção sem avaliar a arquitetura da aplicação**.

---

# 10. Criação do superusuário

O `entrypoint.sh` garante que exista um superusuário Django.

As credenciais são obtidas através das variáveis:

```text
DJANGO_SUPERUSER_USERNAME
DJANGO_SUPERUSER_EMAIL
DJANGO_SUPERUSER_PASSWORD
```

No `docker-compose.yml` atual:

```yaml
environment:
  - DEBUG=1
  - DJANGO_SUPERUSER_USERNAME=admin
  - DJANGO_SUPERUSER_EMAIL=zeloko
  - DJANGO_SUPERUSER_PASSWORD=Industria12!
```

O script não apenas cria o usuário caso ele não exista.

Ele também garante que o usuário esteja com:

```python
is_staff = True
is_superuser = True
```

e atualiza a senha durante a inicialização.

### ⚠️ Segurança

Não utilize uma senha fixa como:

```text
Industria12!
```

em uma instalação pública.

O ideal é alterar a senha e, preferencialmente, retirar credenciais diretamente do `docker-compose.yml`, utilizando um mecanismo apropriado de secrets ou variáveis protegidas.

---

# 11. Docker Compose

O deploy cria automaticamente:

```text
docker-compose.yml
```

A aplicação utiliza a imagem:

```text
zeloko/supermercado-kix:latest
```

e expõe:

```text
8006:8000
```

Portanto:

```text
Host
  │
  │ :8006
  ▼
Docker
  │
  │ :8000
  ▼
Django
```

O container recebe o nome:

```text
Store
```

---

# 12. Dados persistentes

São utilizados dois volumes:

```yaml
volumes:
  - ./data:/app/data
  - ./media:/app/media
```

Isso significa que os dados ficam no diretório da própria instância:

```text
./data
./media
```

Mesmo que o container seja removido e recriado, esses diretórios continuam existindo no host.

A estrutura será:

```text
Hexarcs_loja/
├── data/
│   └── ...
│
└── media/
    └── ...
```

---

# 13. O que acontece ao executar `deploy.sh`

O fluxo completo é:

```text
./deploy.sh
      │
      ├── Cria .env
      │
      ├── Cria entrypoint.sh
      │
      ├── Cria docker-compose.yml
      │
      ├── Dá permissão ao entrypoint
      │
      ├── Para containers anteriores
      │
      └── Sobe o novo container
                    │
                    ▼
              entrypoint.sh
                    │
                    ├── Configura Django
                    ├── Configura Allauth
                    ├── makemigrations
                    ├── migrate
                    ├── Garante superusuário
                    └── runserver
```

---

# 14. Importante: `docker compose down -v`

O deploy contém:

```bash
docker compose down -v || true
```

O comando:

```bash
docker compose down
```

para e remove os containers criados pelo Compose.

Já o:

```bash
-v
```

também remove **volumes Docker nomeados e anônimos associados ao Compose**.

Neste projeto, `data` e `media` são bind mounts:

```yaml
./data:/app/data
./media:/app/media
```

Portanto, eles **não são removidos pelo `down -v`**, pois são diretórios do host e não volumes Docker nomeados.

Mesmo assim, tenha cuidado ao alterar o Compose no futuro e introduzir volumes Docker reais.

---

# 15. Verificar se o container está rodando

Execute:

```bash
docker ps
```

Você deverá encontrar algo semelhante a:

```text
CONTAINER ID   IMAGE                          NAMES
xxxxxxxxxxxx   zeloko/supermercado-kix:latest   Store
```

---

# 16. Visualizar os logs

Para acompanhar a inicialização:

```bash
docker compose logs -f
```

Ou:

```bash
docker logs -f Store
```

Os logs devem mostrar as etapas executadas pelo `entrypoint.sh`, incluindo as migrações e a inicialização do Django.

---

# 17. Verificar o container diretamente

Execute:

```bash
docker compose ps
```

Para entrar no container:

```bash
docker exec -it Store /bin/sh
```

---

# 18. Parar a aplicação

Para parar a loja:

```bash
docker compose down
```

Isso remove o container, mas mantém os diretórios:

```text
data/
media/
```

---

# 19. Reiniciar a aplicação

Depois de uma alteração na configuração:

```bash
docker compose down
docker compose up -d
```

Ou simplesmente:

```bash
docker compose restart
```

---

# 20. Reexecutar o deploy

Como o `deploy.sh` recria os arquivos de configuração, ele pode ser utilizado novamente:

```bash
./deploy.sh
```

O processo irá:

1. recriar o `.env`;
2. recriar o `entrypoint.sh`;
3. recriar o `docker-compose.yml`;
4. parar o container atual;
5. criar um novo container;
6. executar as migrações;
7. garantir o superusuário;
8. iniciar a aplicação.

---

# 21. Instalação completa em uma nova instância

Em uma máquina preparada com Docker e Docker Compose:

```bash
mkdir -p ~/Hexarcs_loja
cd ~/Hexarcs_loja
```

Crie o script:

```bash
nano deploy.sh
```

Cole o `deploy.sh` oficial deste README.

Depois:

```bash
chmod +x deploy.sh
```

E execute:

```bash
./deploy.sh
```

Ao final:

```bash
docker compose ps
```

e:

```bash
docker compose logs -f
```

---

# 22. Acesso à aplicação

A aplicação Django escuta dentro do container na porta:

```text
8000
```

O Docker publica essa porta no host como:

```text
8006
```

Portanto, diretamente pelo servidor:

```text
http://SEU_SERVIDOR:8006
```

Quando houver um Nginx ou outro proxy reverso na frente da aplicação, o acesso normalmente será feito pelo domínio configurado no proxy.

---

# 23. Recomendações antes de produção

Antes de expor essa configuração publicamente, revise principalmente:

### Django

```python
DEBUG = False
```

### Hosts

Evite:

```python
ALLOWED_HOSTS = ['*']
```

Prefira:

```python
ALLOWED_HOSTS = [
    'seu-dominio.com',
]
```

### CSRF

Evite:

```python
CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*']
```

Prefira:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://seu-dominio.com',
]
```

### Secret Key

Não utilize:

```text
django-insecure-...
```

como chave definitiva de produção.

### Senha administrativa

Não mantenha:

```text
Industria12!
```

como senha de produção.

### HTTPS

Utilize HTTPS no domínio público e configure corretamente o proxy reverso.

---

# 24. Resumo

O `deploy.sh` é o **único ponto de entrada necessário para montar a instância da KIX Store**.

Ele gera automaticamente:

```text
deploy.sh
     │
     ├── .env
     ├── entrypoint.sh
     └── docker-compose.yml
```

e inicia:

```text
Docker
  │
  ▼
KIX Store
  │
  ├── Django
  ├── Allauth
  ├── Login local
  ├── Google Login
  ├── Migrações automáticas
  ├── Superusuário automático
  ├── data/
  └── media/
```

Para uma nova instalação, o procedimento básico é simplesmente:

```bash
mkdir -p ~/Hexarcs_loja
cd ~/Hexarcs_loja
nano deploy.sh
chmod +x deploy.sh
./deploy.sh
```

**O `deploy.sh` passa a ser o script oficial de implantação da KIX Store.**

---

# 25. Formulário de contato via Telegram + estáticos em produção

Esta versão adiciona um **formulário de contato no rodapé** que envia a mensagem
diretamente para o Telegram do dono da loja, e prepara a aplicação para produção
(`DEBUG=False`) usando **Whitenoise** para servir os arquivos estáticos.

## Novas variáveis no `.env`

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

- `TELEGRAM_BOT_TOKEN` — token do bot criado no @BotFather.
- `TELEGRAM_CHAT_ID` — ID do chat que receberá as mensagens (ex.: `862995447`).

Essas variáveis têm prioridade sobre o painel admin. Se ficarem vazias, é possível
configurar as mesmas credenciais em **Admin → "Configuração do Telegram"**.

## Novas configurações no painel admin

- **"Configuração do Telegram"** — credenciais (fallback do `.env`) e textos do
  formulário (título, botão, mensagens de sucesso/erro). O campo `ativo` liga/desliga o form.
- **"Configuração do Rodapé"** — dados da empresa (descrição curta, telefone(s),
  e-mail, endereço, site principal) e redes sociais (Facebook, Instagram, YouTube, X).

## Whitenoise e `collectstatic`

Com `DEBUG=False` o Django **não** serve `/static/`. O **Whitenoise** passa a servir
esses arquivos a partir de `staticfiles/`. Por isso, o `entrypoint.sh` executa:

```bash
python manage.py collectstatic --noinput
```

antes de iniciar o servidor.

Já a mídia (`/media/` — imagens de produtos, logo etc.) continua sendo servida pelo
Django (`core/urls.py`), pois o Whitenoise não cobre `/media/`.

## O que muda no `deploy.sh`

- O `.env` gerado agora inclui `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` (vazias).
- O `entrypoint.sh` executa `collectstatic` antes do `runserver`.
- `DEBUG` passa a ser `False` por padrão.
