import json
import os
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import requests
from dotenv import load_dotenv

from .cart import KixCart
from .models import CotacaoBitcoin, Produto, Categoria, HomeConfig, MacroCategoria
from .forms import ProfileForm

load_dotenv()


# def home(request):
#     """Página inicial com a vitrine de produtos dinâmica, cotação BTC/BRL, Hero e Macro Categorias Customizáveis"""
#     agora = timezone.now()
#     vinte_quatro_horas_atras = agora - timedelta(hours=24)

#     registro_cotacao = CotacaoBitcoin.objects.last()

#     if not registro_cotacao or registro_cotacao.ultima_atualizacao < vinte_quatro_horas_atras:
#         try:
#             url = "https://rest.coinapi.io/v1/exchangerate/BTC/BRL"
#             headers = {'X-CoinAPI-Key': os.getenv('COINAPI_KEY', '')}

#             response = requests.get(url, headers=headers, timeout=10)

#             if response.status_code == 200:
#                 data = response.json()
#                 novo_preco = data['rate']

#                 if not registro_cotacao:
#                     registro_cotacao = CotacaoBitcoin.objects.create(
#                         preco_brl=novo_preco,
#                         ultima_atualizacao=agora
#                     )
#                 else:
#                     registro_cotacao.preco_brl = novo_preco
#                     registro_cotacao.ultima_atualizacao = agora
#                     registro_cotacao.save()

#         except Exception as e:
#             print(f"Erro ao buscar cotação na CoinAPI: {e}")

#     produtos_vitrine = Produto.objects.filter(is_promo=True)[:4]
#     hero_config = HomeConfig.objects.filter(ativo=True).first()
#     macro_categorias = MacroCategoria.objects.filter(ativo=True).order_by('ordem')

#     context = {
#         "products": produtos_vitrine,
#         "btc_preco": registro_cotacao.preco_brl if registro_cotacao else None,
#         "ultima_checagem": registro_cotacao.ultima_atualizacao if registro_cotacao else None,
#         "hero_config": hero_config,
#         "macro_categorias": macro_categorias,
#     }
#     return render(request, "index.html", context)

def home(request):
    """Página inicial com a vitrine de produtos dinâmica, cotação BTC/BRL, Hero e Macro Categorias Customizáveis"""
    agora = timezone.now()
    vinte_quatro_horas_atras = agora - timedelta(hours=24)

    registro_cotacao = CotacaoBitcoin.objects.last()

    if not registro_cotacao or registro_cotacao.ultima_atualizacao < vinte_quatro_horas_atras:
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCBRL"
            
            # A Binance não exige headers de autenticação para esta rota pública
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # A Binance retorna o preço dentro da chave 'price' em formato de string
                novo_preco = float(data['price'])

                if not registro_cotacao:
                    registro_cotacao = CotacaoBitcoin.objects.create(
                        preco_brl=novo_preco,
                        ultima_atualizacao=agora
                    )
                else:
                    registro_cotacao.preco_brl = novo_preco
                    registro_cotacao.ultima_atualizacao = agora
                    registro_cotacao.save()

        except Exception as e:
            print(f"Erro ao buscar cotação na Binance: {e}")

    produtos_vitrine = Produto.objects.filter(is_promo=True)[:4]
    hero_config = HomeConfig.objects.filter(ativo=True).first()
    macro_categorias = MacroCategoria.objects.filter(ativo=True).order_by('ordem')

    context = {
        "products": produtos_vitrine,
        "btc_preco": registro_cotacao.preco_brl if registro_cotacao else None,
        "ultima_checagem": registro_cotacao.ultima_atualizacao if registro_cotacao else None,
        "hero_config": hero_config,
        "macro_categorias": macro_categorias,
    }
    return render(request, "index.html", context)


@require_POST
def cart_add(request):
    cart = KixCart(request)
    product_id = request.POST.get("product_id")
    name = request.POST.get("name")
    price_sats = request.POST.get("price_sats")

    if not product_id or not price_sats:
        return JsonResponse({"error": "Dados inválidos ou incompletos."}, status=400)

    cart.add(product_id=product_id, name=name, price_sats=price_sats)

    return JsonResponse({
        "total_items": cart.get_total_items(),
        "total_sats": cart.get_total_sats(),
    })


@require_POST
def cart_remove(request):
    cart = KixCart(request)
    product_id = request.POST.get("product_id")

    if not product_id:
        return JsonResponse({"error": "ID do produto não fornecido."}, status=400)

    cart.remove(product_id=product_id)

    return JsonResponse({
        "total_items": cart.get_total_items(),
        "total_sats": cart.get_total_sats(),
    })


@require_POST
def cart_clear(request):
    cart = KixCart(request)
    cart.clear()

    return JsonResponse({"total_items": 0, "total_sats": 0, "message": "Carrinho limpo com sucesso."})


def cart_status(request):
    cart = KixCart(request)
    return JsonResponse({
        "total_items": cart.get_total_items(),
        "total_sats": cart.get_total_sats(),
        "items": cart.cart,
    })


@require_POST
def generate_lightning_invoice(request):
    cart = KixCart(request)
    total_sats = cart.get_total_sats()

    if total_sats <= 0:
        return JsonResponse({"error": "O carrinho está vazio."}, status=400)

    lnbits_url = os.getenv("LNBITS_URL", "https://engine-1.hexarcs.com/api/v1/payments")
    api_key = os.getenv("LNBITS_API_KEY", "")

    payload = {
        "out": False,
        "amount": total_sats,
        "memo": f"Pedido KIX Supermercado - Total {total_sats} sats",
        "unit": "sat",
    }

    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    try:
        response = requests.post(lnbits_url, json=payload, headers=headers, timeout=10)
        if response.status_code == 201:
            data = response.json()
            return JsonResponse({
                "payment_request": data.get("payment_request"),
                "payment_hash": data.get("payment_hash"),
            })
        else:
            return JsonResponse({"error": "Falha ao gerar cobrança no LNbits."}, status=500)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Erro de conexão com o nó: {str(e)}"}, status=503)


@require_POST
def check_lightning_payment(request):
    try:
        data = json.loads(request.body)
        payment_hash = data.get("payment_hash")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "JSON inválido."}, status=400)

    if not payment_hash:
        return JsonResponse({"error": "Payment hash não fornecido."}, status=400)

    lnbits_base = os.getenv("LNBITS_URL", "https://engine-1.hexarcs.com/api/v1/payments")
    api_url = f"{lnbits_base}/{payment_hash}"
    api_key = os.getenv("LNBITS_API_KEY", "")
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    try:
        requests.get(lnbits_base, headers=headers, timeout=5)
        response = requests.get(api_url, headers=headers, timeout=5)

        if response.status_code == 200:
            payment_data = response.json()
            return JsonResponse({
                "paid": payment_data.get("paid", False),
                "status": payment_data.get("status", "pending"),
            })
        else:
            return JsonResponse({"paid": False, "error": "Não foi possível consultar o LNbits."}, status=response.status_code)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"paid": False, "error": f"Erro de comunicação: {str(e)}"}, status=503)


def categoria_detalhe(request, nome):
    produtos = Produto.objects.filter(categoria__slug=nome)
    return render(request, 'categoria.html', {'nome': nome, 'produtos': produtos})


@login_required
def editar_perfil(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('home') 
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'core/editar_perfil.html', {'form': form})


@login_required
def get_user_profile_api(request):
    profile = getattr(request.user, 'profile', None)
    
    data = {
        'telefone': getattr(profile, 'telefone', 'Não informado') if profile else 'Não informado',
        'endereco': getattr(profile, 'endereco', 'Não informado') if profile else 'Não informado',
    }
    return JsonResponse(data)


from django.shortcuts import get_object_or_404, render
from .models import CategoriaCard, Produto  # Certifique-se de importar seus models

def detalhe_categoria(request, slug):
    # Busca a categoria pelo slug ou retorna erro 404 caso não exista
    categoria = get_object_or_404(CategoriaCard, slug=slug)
    
    # Filtra os produtos vinculados a esta categoria (ajuste o campo FK conforme seu model de Produto)
    produtos = Produto.objects.filter(categoria=categoria)
    
    context = {
        'categoria': categoria,
        'produtos': produtos,
    }
    return render(request, 'categoria.html', context)