from django.conf import settings
from urllib.parse import quote

from .models import CotacaoBitcoin
from .models import SiteConfig
from .models import SiteConfig, ConfiguracaoPix
from .models import ConfiguracaoTelegram, ConfiguracaoRodape
from .models import ConfiguracaoWhatsApp

def btc_context(request):
    """Injeta a última cotação do Bitcoin globalmente em todos os templates"""
    registro_cotacao = CotacaoBitcoin.objects.last()
    return {
        'btc_preco': registro_cotacao.preco_brl if registro_cotacao else 0
    }



def site_config_processor(request):
    return {
        'site_config': SiteConfig.get_solo(),
        'pix_config': ConfiguracaoPix.get_solo()  # <--- Adicionado aqui
    }


from .models import CategoriaCard

def cards_processor(request):
    return {
        'categorias_cards': CategoriaCard.objects.all()
    }


def telegram_config_processor(request):
    """Injeta a configuração do Telegram (credenciais e textos do formulário)."""
    return {
        'telegram_config': ConfiguracaoTelegram.get_solo()
    }


def rodape_config_processor(request):
    """Injeta os dados da empresa exibidos no rodapé."""
    return {
        'rodape_config': ConfiguracaoRodape.get_solo()
    }


WHATSAPP_BASE_URL = "https://api.whatsapp.com/send"


def _parse_bool(value):
    """Converte uma string de ambiente em booleano (mesmo padrão do settings)."""
    return str(value or '').strip().lower() in ('true', '1', 't', 'yes', 'on')


def _normalize_numero(numero):
    """Mantém somente dígitos do número informado (ex.: 5531993791730)."""
    return ''.join(ch for ch in (numero or '') if ch.isdigit())


def whatsapp_config_processor(request):
    """Injeta a configuração efetiva do botão flutuante de WhatsApp.

    Prioridade de cada campo: painel admin (ConfiguracaoWhatsApp); se vazio,
    usa a variável de ambiente correspondente do .env. O link "click-to-chat"
    já é montado com o número normalizado e a mensagem codificada (URL-encoding).
    """
    config = ConfiguracaoWhatsApp.get_solo()

    numero_db = (config.numero or '').strip()
    mensagem_db = (config.mensagem_padrao or '').strip()

    # Fallback do .env quando o admin ainda não preencheu o campo no painel.
    numero = _normalize_numero(numero_db)
    if not numero:
        numero = _normalize_numero(getattr(settings, 'WHATSAPP_NUMERO', ''))

    mensagem = mensagem_db or (getattr(settings, 'WHATSAPP_MENSAGEM_PADRAO', '') or '').strip() or 'Olá'

    # O checkbox do painel manda. O .env (WHATSAPP_ATIVO) só decide o on/off
    # quando a configuração inteira está vindo do .env (bootstrap), isto é,
    # quando não há número salvo no banco.
    if numero_db:
        ativo = config.ativo
    else:
        ativo = _parse_bool(getattr(settings, 'WHATSAPP_ATIVO', ''))

    # Só monta a URL quando existe um número válido.
    url = ''
    if numero:
        url = f"{WHATSAPP_BASE_URL}?phone={numero}&text={quote(mensagem, safe='')}"

    return {
        'whatsapp_config': {
            'ativo': bool(ativo and numero),
            'numero': numero,
            'mensagem': mensagem,
            'url': url,
        }
    }
