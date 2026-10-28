import json
import logging
import os
from datetime import timedelta
from urllib.parse import quote
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import requests
from dotenv import load_dotenv

from .cart import KixCart
from .models import CotacaoBitcoin, Produto, Categoria, HomeConfig, MacroCategoria, Servico, ConfiguracaoWhatsApp
from .forms import ProfileForm
from .services.executor import (
    send_contact_telegram_notification,
    send_telegram_message,
    TelegramNotificationError,
)

load_dotenv()

logger = logging.getLogger(__name__)


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
    servicos_promo = Servico.objects.filter(is_promo=True)
    hero_config = HomeConfig.objects.filter(ativo=True).first()
    macro_categorias = MacroCategoria.objects.filter(ativo=True).order_by('ordem')

    context = {
        "products": produtos_vitrine,
        "servicos_promo": servicos_promo,
        "btc_preco": registro_cotacao.preco_brl if registro_cotacao else None,
        "ultima_checagem": registro_cotacao.ultima_atualizacao if registro_cotacao else None,
        "hero_config": hero_config,
        "macro_categorias": macro_categorias,
    }
    return render(request, "index.html", context)


@require_POST
def cart_add(request):
    cart = KixCart(request)
    product_id = request.POST.get("product_id")  # product_id = SKU do produto

    if not product_id:
        return JsonResponse({"error": "Produto não informado."}, status=400)

    # Preço e nome SEMPRE vêm do banco, nunca do navegador.
    # (evita manipulação de preço no checkout / injeção no nome)
    try:
        produto = Produto.objects.get(sku=product_id)
    except Produto.DoesNotExist:
        return JsonResponse({"error": "Produto não encontrado."}, status=404)

    cart.add(
        product_id=produto.sku,
        name=produto.nome,
        price_sats=produto.preco_sats,
    )

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
    servicos = Servico.objects.filter(categoria__slug=nome)
    return render(request, 'categoria.html', {'nome': nome, 'produtos': produtos, 'servicos': servicos})


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





def obter_carrinho_api(request):
    cart = KixCart(request)
    return JsonResponse(
        cart.get_summary()
    )  # Retorna lista de itens, total de itens e total sats
    
def produto_detalhe(request, sku):
    product = get_object_or_404(Produto, sku=sku)
    return render(request, 'produto_detalhe.html', {'product': product})


# =========================================================================
# FORMULÁRIO DE CONTATO (RODAPÉ) -> TELEGRAM
# =========================================================================

MAX_FIELD_LENGTH = 200
MAX_MESSAGE_LENGTH = 5000


@require_POST
def send_telegram(request):
    """Recebe os dados do formulário de contato e notifica o dono via Telegram.

    A notificação é best-effort: se o Telegram falhar, loga e responde sucesso
    mesmo assim, para não quebrar a experiência do visitante.
    """
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    telegram = (request.POST.get("telegram") or "").strip()
    message = (request.POST.get("message") or "").strip()

    missing = []
    if not name:
        missing.append("Nome")
    if not email:
        missing.append("E-mail")
    elif "@" not in email or "." not in email.split("@")[-1]:
        return JsonResponse(
            {"status": "error", "message": "Informe um e-mail válido."},
            status=400,
        )
    if not message:
        missing.append("Mensagem")

    if missing:
        return JsonResponse(
            {"status": "error",
             "message": f"Preencha o(s) campo(s): {', '.join(missing)}."},
            status=400,
        )

    name = name[:MAX_FIELD_LENGTH]
    email = email[:MAX_FIELD_LENGTH]
    telegram = telegram[:MAX_FIELD_LENGTH]
    message = message[:MAX_MESSAGE_LENGTH]

    try:
        send_contact_telegram_notification(name, email, telegram, message)
    except TelegramNotificationError:
        logger.exception("Falha ao enviar notificação Telegram do contato.")
    except Exception:
        logger.exception("Erro inesperado ao notificar o Telegram.")

    return JsonResponse({
        "status": "success",
        "message": "Mensagem enviada via Telegram! Em breve entraremos em contato.",
    })


# =========================================================================
# INTERESSE EM SERVIÇO (ASSESSORIA/CONCIERGE) -> TELEGRAM OU WHATSAPP
# =========================================================================

def _whatsapp_numero():
    """Número efetivo do WhatsApp (banco tem prioridade; .env é fallback).

    Mantém a mesma regra do whatsapp_config_processor para reaproveitar o
    número configurado no botão flutuante.
    """
    config = ConfiguracaoWhatsApp.get_solo()
    numero = ''.join(ch for ch in (config.numero or '') if ch.isdigit())
    if not numero:
        numero = ''.join(ch for ch in (getattr(settings, 'WHATSAPP_NUMERO', '') or '') if ch.isdigit())
    return numero


@require_POST
def servico_interesse(request):
    """Recebe a mensagem de interesse em um serviço e dispara o contato.

    - canal=whatsapp: devolve a URL click-to-chat para o front abrir em nova aba.
    - canal=telegram: envia a mensagem ao dono via bot (ConfiguracaoTelegram/.env).
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    servico_id = data.get('servico_id') or request.POST.get('servico_id')
    canal = (data.get('canal') or request.POST.get('canal') or '').strip()
    mensagem = (data.get('mensagem') or request.POST.get('mensagem') or '').strip()

    if not servico_id or not mensagem:
        return JsonResponse(
            {"status": "error", "message": "Informe o serviço e a mensagem."},
            status=400,
        )

    if canal not in ('whatsapp', 'telegram'):
        return JsonResponse(
            {"status": "error", "message": "Canal de contato inválido."},
            status=400,
        )

    try:
        servico = Servico.objects.get(pk=servico_id)
    except (Servico.DoesNotExist, ValueError):
        return JsonResponse(
            {"status": "error", "message": "Serviço não encontrado."},
            status=404,
        )

    mensagem = mensagem[:MAX_MESSAGE_LENGTH]

    if canal == 'whatsapp':
        if not servico.whatsapp_ativo:
            return JsonResponse(
                {"status": "error", "message": "Este serviço não está habilitado para WhatsApp."},
                status=400,
            )
        numero = _whatsapp_numero()
        if not numero:
            return JsonResponse(
                {"status": "error", "message": "WhatsApp da loja não configurado."},
                status=400,
            )
        url = f"https://api.whatsapp.com/send?phone={numero}&text={quote(mensagem, safe='')}"
        return JsonResponse({"status": "success", "canal": "whatsapp", "url": url})

    # Telegram
    if not servico.telegram_ativo:
        return JsonResponse(
            {"status": "error", "message": "Este serviço não está habilitado para Telegram."},
            status=400,
        )
    texto = (
        "📬 Interesse em serviço\n"
        "──────────────────────────\n"
        f"🏷️ Serviço: {servico.nome}\n"
        f"💬 Mensagem: {mensagem}"
    )
    try:
        send_telegram_message(texto)
    except TelegramNotificationError:
        logger.exception("Falha ao notificar Telegram sobre interesse em serviço.")
        return JsonResponse(
            {"status": "error", "message": "Não foi possível enviar agora. Tente novamente."},
            status=502,
        )

    return JsonResponse({
        "status": "success",
        "canal": "telegram",
        "message": "Mensagem enviada! Em breve entraremos em contato.",
    })