from .models import CotacaoBitcoin
from .models import SiteConfig
from .models import SiteConfig, ConfiguracaoPix
from .models import ConfiguracaoTelegram, ConfiguracaoRodape

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
