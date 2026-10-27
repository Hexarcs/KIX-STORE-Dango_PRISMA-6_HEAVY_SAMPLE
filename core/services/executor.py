"""Serviço de envio de notificações via Telegram Bot API (HTTP puro).

As credenciais seguem a seguinte prioridade:
    1. Variáveis de ambiente / .env (settings.TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    2. ConfiguracaoTelegram salva no painel admin

A biblioteca `requests` é importada de forma tardia para que uma eventual
ausência dela só afete o envio por Telegram, sem derrubar a inicialização
do Django.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotificationError(Exception):
    """Falha ao enviar uma notificação via Telegram Bot API."""


def _resolve_credentials():
    """Retorna a tupla (bot_token, chat_id) combinando .env e painel admin."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "") or ""

    if bot_token and chat_id:
        return bot_token, chat_id

    try:
        from core.models import ConfiguracaoTelegram

        config = ConfiguracaoTelegram.get_solo()
        return bot_token or config.bot_token, chat_id or config.chat_id
    except Exception:
        logger.exception("Falha ao carregar ConfiguracaoTelegram do banco.")
        return bot_token, chat_id


def send_telegram_message(text, *, chat_id=None, bot_token=None, timeout=None):
    """Envia `text` para o chat configurado. Levanta TelegramNotificationError em falha."""
    env_token, env_chat = _resolve_credentials()
    bot_token = bot_token or env_token
    chat_id = chat_id or env_chat
    timeout = getattr(settings, "TELEGRAM_TIMEOUT", 10) if timeout is None else timeout

    if not bot_token or not chat_id:
        raise TelegramNotificationError(
            "Credenciais do Telegram ausentes. Configure o .env ou o painel admin."
        )

    try:
        import requests
    except ImportError as exc:
        raise TelegramNotificationError(
            "A biblioteca 'requests' não está instalada (pip install requests)."
        ) from exc

    url = TELEGRAM_API_URL.format(token=bot_token)
    payload = {"chat_id": chat_id, "text": text}

    try:
        response = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise TelegramNotificationError(
            f"Falha de rede/timeout ao chamar a Telegram Bot API: {exc}"
        ) from exc

    try:
        data = response.json()
    except ValueError:
        data = {}

    # O Telegram sinaliza erro de duas formas: HTTP != 200 e/ou {"ok": false}.
    if response.status_code != 200 or not data.get("ok"):
        description = data.get("description") or response.text or "sem descrição"
        raise TelegramNotificationError(
            f"Telegram recusou (HTTP {response.status_code}): {description}"
        )

    return data


def send_contact_telegram_notification(name, email, telegram, message, **kwargs):
    """Formata os dados de contato e envia para o dono do site via Telegram."""
    telegram = (telegram or "").strip() or "não informado"
    text = (
        "📬 Novo contato pelo site\n"
        "──────────────────────────────\n"
        f"👤 Nome: {name}\n"
        f"📧 E-mail: {email}\n"
        f"💬 Telegram/WhatsApp: {telegram}\n"
        "──────────────────────────────\n"
        "📝 Mensagem:\n"
        f"{message}"
    )
    return send_telegram_message(text, **kwargs)
