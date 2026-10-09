import decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Categoria(models.Model):
    """Define as categorias da loja."""
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Ex: frescos, mercearia, higiene, limpeza")

    def __str__(self):
        return self.nome


class MacroCategoria(models.Model):
    """Define as macro categorias exibidas na vitrine principal."""
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Macro Categoria"
        verbose_name_plural = "Macro Categorias"
        ordering = ['ordem']

    def __str__(self):
        return self.nome


class CotacaoBitcoin(models.Model):
    """Armazena a última cotação do Bitcoin obtida via API."""
    preco_brl = models.DecimalField(max_digits=12, decimal_places=2)
    ultima_atualizacao = models.DateTimeField()

    def __str__(self):
        return f"BTC: R$ {self.preco_brl} em {self.ultima_atualizacao}"


class Produto(models.Model):
    sku = models.CharField(
        max_length=50, 
        unique=True, # Adicionado unique=True se for usar SKU na URL
        null=True, 
        blank=True, 
        help_text="Identificador único para o JS. Ex: prod_cafe_500"
    )
    nome = models.CharField(max_length=255)
    
    # NOVO CAMPO: Descrição detalhada do produto
    descricao = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Descrição do Produto"
    )
    
    # Ligação com a Categoria
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='produtos'
    )

    icone = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Insira um Emoji correspondente (ex: ☕, 🥫)",
    )

    preco_sats = models.IntegerField(verbose_name="Preço em Satoshis (Sats)")

    imagem = models.ImageField(
        upload_to="produtos/",
        blank=True,
        null=True,
        verbose_name="Foto do Produto (Quadrada)",
    )

    is_promo = models.BooleanField(
        default=False, verbose_name="Exibir em Ofertas Rápidas (Máx 4)"
    )

    def __str__(self):
        return self.nome

    @property
    def preco_brl(self):
        ultima_cotacao = CotacaoBitcoin.objects.last()
        if ultima_cotacao and ultima_cotacao.preco_brl > 0:
            valor_sat_em_brl = ultima_cotacao.preco_brl / decimal.Decimal("100000000")
            preco_calculado = decimal.Decimal(self.preco_sats) * valor_sat_em_brl
        else:
            fallback_sat_em_brl = decimal.Decimal("0.005")
            preco_calculado = decimal.Decimal(self.preco_sats) * fallback_sat_em_brl

        return preco_calculado.quantize(decimal.Decimal("0.01"))

    @property
    def preco_pix_estatal(self):
        valor_inflacionado = self.preco_brl * decimal.Decimal("1.1")
        return valor_inflacionado.quantize(decimal.Decimal("0.01"))


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    endereco = models.TextField(verbose_name="Endereço Completo", blank=True, null=True)
    telefone = models.CharField(max_length=20, verbose_name="WhatsApp", blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


# =========================================================================
# SIGNALS: Garante a existência do Profile de forma segura contra falhas
# =========================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria o Profile automaticamente ao registrar um novo User."""
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Garante que o perfil exista e seja salvo ao atualizar o User."""
    profile, _ = Profile.objects.get_or_create(user=instance)
    profile.save()
    
    
# =========================================================================
# CONFIGURAÇÃO DO HERO (HOME)
# =========================================================================    

class HomeConfig(models.Model):
    titulo_hero = models.CharField(max_length=200, default="Bem-vindo ao Supermercado Kix", verbose_name="Título do Hero")
    subtitulo_hero = models.TextField(blank=True, null=True, verbose_name="Subtítulo do Hero")
    imagem_hero = models.ImageField(upload_to='hero/', verbose_name="Imagem do Hero")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Configuração do Hero (Home)"
        verbose_name_plural = "Configurações do Hero (Home)"

    def __str__(self):
        return "Banner Hero da Home"

#==============================bagde e nome do site===================

#from django.db import models

class SiteConfig(models.Model):
    # SEO e Nomenclatura
    logo = models.ImageField(upload_to='site/', blank=True, null=True, verbose_name="Logo do Site")
    meta_title = models.CharField(max_length=150, default="Supermercado Itatingax - Economia Real no Ecossistema")
    nome_loja = models.CharField(max_length=100, default="Supermercado Itatingax")
    
    # Textos e Cores da Badge
    badge_ecossistema = models.CharField(max_length=100, default="Membro do Ecossistema KIX")
    badge_bg_color = models.CharField(max_length=7, default="#f7931a", help_text="Cor de fundo da Badge (Hex: #f7931a)")
    badge_text_color = models.CharField(max_length=7, default="#000000", help_text="Cor do texto da Badge (Hex: #000000)")

    # Estilização Geral do Header
    header_bg_color = models.CharField(max_length=7, default="#1a1a1a", help_text="Cor de fundo (Hex: #1a1a1a)")
    header_text_color = models.CharField(max_length=7, default="#ffffff", help_text="Cor do texto principal")
    sats_color = models.CharField(max_length=7, default="#f7931a", help_text="Cor da palavra Sats (Hex: #f7931a)")

    # Textos e Cores do Carrinho
    btn_clear_text = models.CharField(max_length=30, default="🗑️ Limpar")
    btn_clear_color = models.CharField(max_length=7, default="#ff4d4d", help_text="Cor do botão Limpar")
    
    btn_pay_text = models.CharField(max_length=30, default="Pagar")
    btn_pay_bg = models.CharField(max_length=7, default="#28a745", help_text="Fundo do botão Pagar")
    btn_pay_color = models.CharField(max_length=7, default="#ffffff", help_text="Texto do botão Pagar")

    # Textos e Cores da Autenticação (Logado)
    auth_greeting = models.CharField(max_length=30, default="Olá,")
    btn_edit_text = models.CharField(max_length=30, default="Editar Endereço")
    btn_edit_color = models.CharField(max_length=7, default="#f7931a", help_text="Cor da borda/texto de Editar")
    btn_logout_text = models.CharField(max_length=30, default="Sair")
    btn_logout_bg = models.CharField(max_length=7, default="#dc3545", help_text="Fundo do botão Sair")
    btn_logout_color = models.CharField(max_length=7, default="#ffffff", help_text="Texto do botão Sair")

    # Textos e Cores da Autenticação (Deslogado)
    btn_login_text = models.CharField(max_length=50, default="Entrar com o Google")
    btn_login_fallback_text = models.CharField(max_length=50, default="Entrar")
    btn_login_bg = models.CharField(max_length=7, default="#4285f4", help_text="Fundo do botão Entrar")
    btn_login_color = models.CharField(max_length=7, default="#ffffff", help_text="Texto do botão Entrar")

    # Configurações do Banner (Textos e Exibição)
    exibir_banner = models.BooleanField(default=True, help_text="Exibir o banner promocional no topo?")
    exibir_cotacao = models.BooleanField(default=True, help_text="Exibir a cotação do Bitcoin dentro do banner?")
    
    banner_titulo = models.CharField(max_length=150, default="⚡ Pagamento Nativo em Satoshis")
    banner_texto = models.TextField(default="Logística integrada ao Ecossistema KIX. Economia real direto no caixa utilizando a eficiência da Lightning Network.")
    banner_texto_cotacao = models.CharField(max_length=50, default="Preço atual do Bitcoin:")
    banner_texto_economia = models.TextField(default="💡 É possível pagar utilizando o Pix estatal, mas o valor pagando direto em Satoshis é 10% menor!")

    # Estilização do Banner (Cores)
    banner_bg_color = models.CharField(max_length=7, default="#222222", help_text="Cor de fundo do banner (Hex: #222222)")
    banner_title_color = models.CharField(max_length=7, default="#ffffff", help_text="Cor do título do banner")
    banner_text_color = models.CharField(max_length=7, default="#dddddd", help_text="Cor do texto descritivo")
    banner_border_color = models.CharField(max_length=30, default="rgba(255,255,255,0.2)", help_text="Cor da linha divisória (Hex ou RGBA)")
    banner_cotacao_color = models.CharField(max_length=7, default="#ffffff", help_text="Cor do texto do preço do BTC")
    banner_economia_color = models.CharField(max_length=7, default="#ffb703", help_text="Cor da mensagem de economia (Hex: #ffb703)")

    def save(self, *args, **kwargs):
        # Garante que sempre haverá apenas uma linha de configuração (Singleton)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configurações do Site"
    
    
#---------categorias------------------

from django.db import models

class CategoriaCard(models.Model):
    titulo = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Ex: frescos, mercearia, higiene, limpeza")
    imagem_fundo = models.ImageField(upload_to='banners_cards/', help_text="Imagem de fundo do card")
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return self.titulo    





# =========================================================================
# CONFIGURAÇÃO DO PIX
# =========================================================================

class ConfiguracaoPix(models.Model):
    """Configurações centralizadas do PIX para destaque no Admin."""
    
    chave_pix = models.CharField(
        max_length=255,
        default="SUA_CHAVE_PIX_AQUI",
        verbose_name="Chave PIX (E-mail, CPF, CNPJ ou Aleatória)",
        help_text="Chave PIX que será exibida para o cliente realizar o pagamento."
    )
    nome_titular = models.CharField(
        max_length=100,
        default="Supermercado Itatingax",
        verbose_name="Nome do Titular/Recebedor",
        help_text="Nome da conta que aparecerá no comprovante do cliente."
    )
    
    # NEW: Novo campo para personalizar o texto da taxa
    rotulo_taxa_pix = models.CharField(
        max_length=100,
        default="Taxa de Processamento Fiat (PIX)",
        verbose_name="Rótulo / Nome da Taxa",
        help_text="Texto que aparece antes do valor da taxa. Ex: Taxa de Processamento Fiat, Taxa de Submissão Estatal, Taxa de Conveniência"
    )
    
    taxa_estatal_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name="Taxa da Operação Fiat (%)",
        help_text="Porcentagem de taxa cobrada no checkout PIX (ex: 10.00 para +10%)."
    )
    instrucao_pagamento = models.TextField(
        default="Envie o valor exato em Reais.",
        verbose_name="Mensagem / Aviso do Modal",
        help_text="Texto explicativo mostrado na parte inferior do modal PIX."
    )

    class Meta:
        verbose_name = "Configuração do PIX"
        verbose_name_plural = "Configuração do PIX"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Configuração PIX ({self.chave_pix})"

