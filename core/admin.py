from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Produto, Categoria, CotacaoBitcoin, Profile # Importe o Profile aqui
from .models import HomeConfig

# 1. Define o Inline para o Profile aparecer dentro do User
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Informações Adicionais (Entrega/Contato)'

# 2. Desregistra o User padrão e registra o customizado
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

# Seus modelos originais permanecem aqui:
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sku', 'icone', 'categoria', 'preco_sats', 'exibir_preco_brl', 'is_promo')
    list_editable = ('is_promo', 'categoria')
    search_fields = ('nome', 'sku')
    list_filter = ('is_promo', 'categoria')

    def exibir_preco_brl(self, obj):
        return f"R$ {obj.preco_brl}"
    exibir_preco_brl.short_description = 'Preço Estimado (R$)'

@admin.register(CotacaoBitcoin)
class CotacaoBitcoinAdmin(admin.ModelAdmin):
    list_display = ('preco_brl', 'ultima_atualizacao')
    
    
@admin.register(HomeConfig)
class HomeConfigAdmin(admin.ModelAdmin):
    list_display = ('titulo_hero', 'ativo')    
    
    
#from django.contrib import admin
from .models import SiteConfig

@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
         ('Configurações de Header e SEO', {
            'fields': ('meta_title', 'nome_loja', 'logo', 'badge_ecossistema')
        }),
        
        ('Configurações do Banner (Textos e Exibição)', {
            'fields': (
                ('exibir_banner', 'exibir_cotacao'),
                'banner_titulo', 'banner_texto', 
                'banner_texto_cotacao', 'banner_texto_economia'
            )
        }),
        
        ('Estilização do Banner (Cores)', {
            'fields': (
                'banner_bg_color', 'banner_title_color', 'banner_text_color',
                'banner_border_color', 'banner_cotacao_color', 'banner_economia_color'
            )
        }),

        ('Estilização do Header (Cores e Layout)', {
            'fields': ('header_bg_color', 'header_text_color', 'sats_color')
        }),
        
        ('Botões do Carrinho (Textos e Cores)', {
            'fields': (
                ('btn_clear_text', 'btn_clear_color'),
                ('btn_pay_text', 'btn_pay_bg', 'btn_pay_color')
            )
        }),
        
        ('Autenticação - Usuário Logado', {
            'fields': (
                'auth_greeting',
                ('btn_edit_text', 'btn_edit_color'),
                ('btn_logout_text', 'btn_logout_bg', 'btn_logout_color')
            )
        }),
        
        ('Autenticação - Visitante', {
            'fields': (
                'btn_login_text', 'btn_login_fallback_text', 
                ('btn_login_bg', 'btn_login_color')
            )
        }),
        
    )

    def has_add_permission(self, request):
        # Impede criar mais de uma instância de configuração
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Impede deletar o registro de configuração principal
        return False
    
    
from .models import CategoriaCard

@admin.register(CategoriaCard)
class CategoriaCardAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'ordem')
    prepopulated_fields = {'slug': ('titulo',)}    
    
    
    
    
from .models import ConfiguracaoPix

@admin.register(ConfiguracaoPix)
class ConfiguracaoPixAdmin(admin.ModelAdmin):
    list_display = ('chave_pix', 'nome_titular', 'rotulo_taxa_pix', 'taxa_estatal_percentual')
    
    fieldsets = (
        ('Chave e Recebedor', {
            'fields': ('chave_pix', 'nome_titular')
        }),
        ('Nomenclatura e Taxas', {
            'fields': ('rotulo_taxa_pix', 'taxa_estatal_percentual', 'instrucao_pagamento')
        }),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False