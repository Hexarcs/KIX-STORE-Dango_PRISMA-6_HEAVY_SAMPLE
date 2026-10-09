from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importe o módulo views inteiro desta forma:
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    
    # Agora você pode acessar tudo via 'views.nome_da_funcao'
    path('', views.home, name='home'),
    
    # Rotas do Carrinho
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    path('cart/status/', views.cart_status, name='cart_status'),
    path('cart/checkout/', views.generate_lightning_invoice, name='cart_checkout'), 
    path('cart/check-payment/', views.check_lightning_payment, name='check_payment'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('api/user-profile/', views.get_user_profile_api, name='user_profile_api'),
    
    # Rota da Categoria
    path('categoria/<str:nome>/', views.categoria_detalhe, name='categoria_detalhe'),
    path('categoria/<slug:slug>/', views.detalhe_categoria, name='categoria_detalhe'),
    path('cart/summary/', views.obter_carrinho_api, name='cart_summary'),
    path('produto/<str:sku>/', views.produto_detalhe, name='produto_detalhe'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)