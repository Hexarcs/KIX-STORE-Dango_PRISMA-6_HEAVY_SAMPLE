from .models import CotacaoBitcoin
from .models import SiteConfig
from .models import SiteConfig, ConfiguracaoPix

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