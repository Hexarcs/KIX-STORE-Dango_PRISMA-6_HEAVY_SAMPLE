// ==========================================
// 1. CONFIGURAÇÕES INICIAIS E CSRF TOKEN
// ==========================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
window.csrfToken = getCookie('csrftoken');


// ==========================================
// 2. CARREGAMENTO DE DADOS DO USUÁRIO
// ==========================================
function loadUserData() {
    fetch('/api/user-profile/') 
    .then(r => r.json())
    .then(data => {
        const phoneEl = document.getElementById('user-phone');
        const addressEl = document.getElementById('user-address');
        if (phoneEl) phoneEl.innerText = data.telefone || 'Não informado';
        if (addressEl) addressEl.innerText = data.endereco || 'Não informado';
    })
    .catch(err => console.error("Erro ao carregar perfil:", err));
}


// ==========================================
// 3. LÓGICA DE ALTERNÂNCIA DE TEMA
// ==========================================
const themeToggleBtn = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        if (currentTheme === 'light') {
            htmlElement.setAttribute('data-theme', 'dark');
            themeToggleBtn.innerText = '☀️';
        } else {
            htmlElement.setAttribute('data-theme', 'light');
            themeToggleBtn.innerText = '🌙';
        }
    });
}


// ==========================================
// 4. ATUALIZAÇÃO DA UI DO CARRINHO (WIDGETS & LISTAS)
// ==========================================
function updateGlobalCartUI(totalItems, totalSats) {
    const counterEl = document.getElementById('cart-counter');
    const totalSatsEl = document.getElementById('cart-total-sats');
    const btnPay = document.getElementById('btn-pay');
    const btnClear = document.getElementById('btn-clear-cart');

    if (counterEl) counterEl.innerText = totalItems;
    if (totalSatsEl) totalSatsEl.innerText = totalSats.toLocaleString('pt-BR');

    if (totalItems > 0) {
        if (btnPay) btnPay.style.display = 'inline-block';
        if (btnClear) btnClear.style.display = 'inline-block';
    } else {
        if (btnPay) btnPay.style.display = 'none';
        if (btnClear) btnClear.style.display = 'none';
    }
}

// Renderiza a lista detalhada dos itens dentro dos modais de pagamento (KIX e PIX)
function atualizarListasModal(itensCarrinho) {
    const kixContainer = document.getElementById('kix-items-list');
    const pixContainer = document.getElementById('pix-items-list');

    if (!kixContainer && !pixContainer) return;

    // Normaliza para Array caso venha como Objeto do backend
    const lista = Array.isArray(itensCarrinho) 
        ? itensCarrinho 
        : (itensCarrinho ? Object.values(itensCarrinho) : []);

    if (lista.length === 0) {
        const vazioHtml = '<p style="margin:0; color:#888;">Nenhum item selecionado.</p>';
        if (kixContainer) kixContainer.innerHTML = vazioHtml;
        if (pixContainer) pixContainer.innerHTML = vazioHtml;
        return;
    }

    let htmlItensKix = '';
    let htmlItensPix = '';

    lista.forEach(item => {
        const subtotal = item.subtotal_sats ?? ((item.price_sats || 0) * (item.quantity || 1));
        const subtotalFormatado = Number(subtotal).toLocaleString('pt-BR');

        // Formato para KIX (Lightning)
        htmlItensKix += `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span>${item.name} <small style="color:#888;">(x${item.quantity})</small></span>
                <strong style="color: #f2a900;">${subtotalFormatado} sats</strong>
            </div>
        `;

        // Formato para PIX Estatal
        htmlItensPix += `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span>${item.name} <small style="color:#888;">(x${item.quantity})</small></span>
                <strong style="color: #32b3a2;">${subtotalFormatado} sats</strong>
            </div>
        `;
    });

    if (kixContainer) kixContainer.innerHTML = htmlItensKix;
    if (pixContainer) pixContainer.innerHTML = htmlItensPix;
}

// Sincroniza o estado completo do carrinho junto ao backend
function fetchCartStatus() {
    return fetch('/cart/status/')
    .then(response => response.json())
    .then(data => {
        updateGlobalCartUI(data.total_items || 0, data.total_sats || 0);

        if (data.items) {
            // Atualiza contadores individuais na vitrine
            const itemsEntries = Array.isArray(data.items) 
                ? data.items.map(i => [i.product_id || i.id, i])
                : Object.entries(data.items);

            itemsEntries.forEach(([prodId, item]) => {
                const qtySpan = document.getElementById(`qty_${prodId}`);
                if (qtySpan) {
                    qtySpan.innerText = item.quantity || 0;
                }
            });

            atualizarListasModal(data.items);
        } else {
            atualizarListasModal([]);
        }
    })
    .catch(error => console.error('Erro ao carregar status do carrinho:', error));
}


// ==========================================
// 5. AÇÕES DO CARRINHO (+, -, LIMPAR)
// ==========================================
document.querySelectorAll('.btn-add').forEach(button => {
    button.addEventListener('click', function() {
        const productId = this.getAttribute('data-product-id');
        const formData = new FormData();
        formData.append('product_id', productId);
        formData.append('name', this.getAttribute('data-name'));
        formData.append('price_sats', this.getAttribute('data-price-sats'));

        this.disabled = true;

        fetch('/cart/add/', {
            method: 'POST',
            headers: { 'X-CSRFToken': window.csrfToken },
            body: formData
        })
        .then(response => {
            if (!response.ok) throw new Error('Erro na requisição');
            return response.json();
        })
        .then(data => {
            if (data.total_items !== undefined) {
                updateGlobalCartUI(data.total_items, data.total_sats);
                const qtySpan = document.getElementById(`qty_${productId}`);
                if (qtySpan) {
                    qtySpan.innerText = parseInt(qtySpan.innerText || '0') + 1;
                }
                fetchCartStatus(); // Atualiza as listas do modal
            }
            this.disabled = false;
        })
        .catch(error => {
            console.error('Erro ao adicionar item:', error);
            this.disabled = false;
        });
    });
});

document.querySelectorAll('.btn-remove').forEach(button => {
    button.addEventListener('click', function() {
        const productId = this.getAttribute('data-product-id');
        if (!productId) return;

        const qtySpan = document.getElementById(`qty_${productId}`);
        if (!qtySpan || parseInt(qtySpan.innerText || '0') <= 0) return;

        const formData = new FormData();
        formData.append('product_id', productId);

        this.disabled = true;

        fetch('/cart/remove/', {
            method: 'POST',
            headers: { 'X-CSRFToken': window.csrfToken },
            body: formData
        })
        .then(response => {
            if (!response.ok) throw new Error('Erro na requisição');
            return response.json();
        })
        .then(data => {
            if (data.total_items !== undefined) {
                updateGlobalCartUI(data.total_items, data.total_sats);
                const currentQty = parseInt(qtySpan.innerText || '0');
                qtySpan.innerText = currentQty > 0 ? currentQty - 1 : 0;
                fetchCartStatus(); // Atualiza as listas do modal
            }
            this.disabled = false;
        })
        .catch(error => {
            console.error('Erro ao remover item:', error);
            this.disabled = false;
        });
    });
});

const btnClearCart = document.getElementById('btn-clear-cart');
if (btnClearCart) {
    btnClearCart.addEventListener('click', function() {
        if (!confirm('Deseja realmente esvaziar o seu carrinho?')) return;

        this.disabled = true;

        fetch('/cart/clear/', {
            method: 'POST',
            headers: { 'X-CSRFToken': window.csrfToken }
        })
        .then(response => {
            if (!response.ok) throw new Error('Erro na requisição');
            return response.json();
        })
        .then(() => {
            updateGlobalCartUI(0, 0);
            document.querySelectorAll('.product-qty').forEach(qtySpan => {
                qtySpan.innerText = '0';
            });
            atualizarListasModal([]);
            this.disabled = false;
        })
        .catch(error => {
            console.error('Erro ao limpar carrinho:', error);
            this.disabled = false;
        });
    });
}


// ==========================================
// 6. CONTROLE DO MODAL E CHECKOUT LIGHTNING / PIX
// ==========================================
const modal = document.getElementById('pay-modal');
const btnPay = document.getElementById('btn-pay');
const closeModal = document.querySelector('.close-modal');
const btnConfirmMock = document.getElementById('btn-confirm-mock');
const btnRetryInvoice = document.getElementById('btn-retry-invoice');
const invoiceTextDiv = document.querySelector('.invoice-text');
const qrContainer = document.querySelector('.qr-container');

// Elementos das Etapas do Modal
const stepConfirm = document.getElementById('step-confirm-address');
const stepPayment = document.getElementById('step-payment');
const stepPixEstatal = document.getElementById('step-pix-estatal');
const btnPixEstatal = document.getElementById('btn-pix-estatal');

let paymentHash = null;    
let checkInterval = null;  
let checkCount = 0;        

// FUNÇÃO PARA GERAR A INVOICE (KIX NATÍVO - LIGHTNING)
function fetchLightningInvoice() {
    if (invoiceTextDiv) invoiceTextDiv.innerText = "Gerando invoice na Lightning Network...";
    if (qrContainer) qrContainer.innerHTML = "<span style='color:var(--texto-secundario); font-size:14px;'>Aguardando dados...</span>";
    if (btnRetryInvoice) btnRetryInvoice.style.display = 'none';
    if (btnConfirmMock) btnConfirmMock.style.display = 'none';

    const cartTotalEl = document.getElementById('cart-total-sats');
    const displaySatsEl = document.getElementById('modal-total-sats-display');
    const modalTotalEl = document.getElementById('modal-total-sats');

    if (cartTotalEl) {
        if (displaySatsEl) displaySatsEl.innerText = cartTotalEl.innerText;
        if (modalTotalEl) modalTotalEl.innerText = cartTotalEl.innerText;
    }

    if (checkInterval) clearInterval(checkInterval);
    paymentHash = null;

    fetch('/cart/checkout/', {
        method: 'POST',
        headers: { 'X-CSRFToken': window.csrfToken }
    })
    .then(response => {
        if (!response.ok) throw new Error('Erro ao gerar invoice');
        return response.json();
    })
    .then(data => {
        if (data.payment_request && data.payment_hash) {
            if (invoiceTextDiv) invoiceTextDiv.innerText = data.payment_request;
            paymentHash = data.payment_hash; 

            // Geração do QR Code
            if (qrContainer && typeof qrcode !== 'undefined') {
                const qr = qrcode(0, 'L');
                qr.addData(data.payment_request);
                qr.make();
                qrContainer.innerHTML = qr.createImgTag(4);

                const qrImg = qrContainer.querySelector('img');
                if (qrImg) {
                    qrImg.style.background = '#ffffff';
                    qrImg.style.padding = '10px';
                    qrImg.style.borderRadius = '8px';
                }
            }

            if (btnConfirmMock) btnConfirmMock.style.display = 'block';
            startCheckingPayment();
        } else {
            throw new Error('Dados incompletos');
        }
    })
    .catch(error => {
        console.error('Erro no checkout:', error);
        if (invoiceTextDiv) invoiceTextDiv.innerText = "Falha temporária ao conectar com o servidor LNbits. Quer tentar de novo?";
        if (qrContainer) qrContainer.innerHTML = "<span style='color:#e74c3c; font-size:14px;'>❌ Falha ao carregar QR Code</span>";
        if (btnRetryInvoice) btnRetryInvoice.style.display = 'block';
    });
}

// FUNÇÕES DE VERIFICAÇÃO DE PAGAMENTO
function startCheckingPayment() {
    checkCount = 0;
    if (checkInterval) clearInterval(checkInterval);
    checkInterval = setInterval(checkStatusOnBackend, 3000); 
}

function checkStatusOnBackend() {
    if (!paymentHash) return;
    checkCount++;

    fetch('/cart/check-payment/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        },
        body: JSON.stringify({ payment_hash: paymentHash })
    })
    .then(response => response.json())
    .then(data => {
        if (data.paid) {
            clearInterval(checkInterval);
            if (invoiceTextDiv) invoiceTextDiv.innerHTML = "<strong style='color:#27ae60;'>🎉 PAGAMENTO CONFIRMADO COM SUCESSO!</strong>";
            if (qrContainer) qrContainer.innerHTML = "<span style='font-size:48px;'>✅</span>";
            if (btnConfirmMock) btnConfirmMock.style.display = 'none';

            setTimeout(() => {
                alert('Obrigado! Seu pagamento em Satoshis foi confirmado na Lightning Network.');
                if (modal) modal.style.display = 'none';
                const clearCartBtn = document.getElementById('btn-clear-cart');
                if (clearCartBtn) clearCartBtn.click();
            }, 1000);

        } else if (checkCount >= 60) { 
            clearInterval(checkInterval);
            if (invoiceTextDiv) invoiceTextDiv.innerHTML = "<strong style='color:#e74c3c;'>⌛ Tempo limite esgotado. A invoice expirou.</strong>";
            if (btnRetryInvoice) btnRetryInvoice.style.display = 'block';
        } else {
            console.log(`Verificando pagamento... Tentativa ${checkCount}`);
        }
    })
    .catch(err => console.error("Erro ao checar status:", err));
}

// ==========================================
// EVENTOS DE CLIQUE DO FLUXO DO MODAL
// ==========================================

if (btnPay) {
    btnPay.addEventListener('click', () => {
        if (stepPayment) stepPayment.style.display = 'none';
        if (stepPixEstatal) stepPixEstatal.style.display = 'none';
        if (stepConfirm) stepConfirm.style.display = 'block';

        const cartTotalEl = document.getElementById('cart-total-sats');
        const modalTotalEl = document.getElementById('modal-total-sats');

        if (cartTotalEl && modalTotalEl) {
            modalTotalEl.innerText = cartTotalEl.innerText;
        }

        loadUserData();
        fetchCartStatus(); // Garante lista atualizada antes de abrir
        if (modal) modal.style.display = 'flex';
    });
}

const btnProceedToPayment = document.getElementById('btn-proceed-to-payment');
if (btnProceedToPayment) {
    btnProceedToPayment.addEventListener('click', () => {
        if (stepConfirm) stepConfirm.style.display = 'none';
        if (stepPayment) stepPayment.style.display = 'block';
        fetchLightningInvoice();
    });
}

if (btnPixEstatal) {
    btnPixEstatal.addEventListener('click', () => {
        const cartTotalEl = document.getElementById('cart-total-sats');
        if (!cartTotalEl) {
            alert("Erro: Carrinho não encontrado na página.");
            return;
        }

        const rawSatsText = cartTotalEl.innerText.replace(/\./g, '');
        const totalSats = parseInt(rawSatsText) || 0;

        const btcPriceInput = document.getElementById('btc-price-hidden');
        const btcPrice = btcPriceInput ? parseFloat(btcPriceInput.value) : 0;

        if (btcPrice <= 0 || totalSats <= 0) {
            alert("Erro ao ler cotação de moedas. Verifique se há itens no carrinho.");
            return;
        }

        // Aplica taxa/imposto de 10%
        const satsComTaxa = totalSats * 1.10;
        
        // Converte Sats para Real
        const totalReais = (satsComTaxa / 100000000) * btcPrice;

        const subtotalSatsEl = document.getElementById('pix-subtotal-sats');
        const btcCotacaoEl = document.getElementById('pix-btc-cotacao');
        const totalReaisEl = document.getElementById('pix-total-reais');

        if (subtotalSatsEl) subtotalSatsEl.innerText = totalSats.toLocaleString('pt-BR');
        if (btcCotacaoEl) btcCotacaoEl.innerText = btcPrice.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (totalReaisEl) totalReaisEl.innerText = totalReais.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        // Gerar QR Code do PIX
        const pixQrContainer = document.querySelector('.pix-qr-container');
        if (pixQrContainer && typeof qrcode !== 'undefined') {
            const qrPix = qrcode(0, 'L');
            qrPix.addData('pereelt@gmail.com');
            qrPix.make();

            pixQrContainer.innerHTML = qrPix.createImgTag(4);

            const qrImg = pixQrContainer.querySelector('img');
            if (qrImg) {
                qrImg.style.background = '#ffffff';
                qrImg.style.padding = '10px';
                qrImg.style.borderRadius = '8px';
                qrImg.style.margin = '0 auto';
                qrImg.style.display = 'block';
            }
        }

        if (stepConfirm) stepConfirm.style.display = 'none';
        if (stepPixEstatal) stepPixEstatal.style.display = 'block';
    });
}

if (btnRetryInvoice) btnRetryInvoice.addEventListener('click', fetchLightningInvoice);

if (closeModal) {
    closeModal.addEventListener('click', () => {
        if (modal) modal.style.display = 'none';
        if (checkInterval) clearInterval(checkInterval);
    });
}

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        if (modal) modal.style.display = 'none';
        if (checkInterval) clearInterval(checkInterval);
    }
});

if (btnConfirmMock) {
    btnConfirmMock.addEventListener('click', () => {
        alert('Simulação manual aceita. Aguardando processamento da rede...');
    });
}


// ==========================================
// 7. INICIALIZAÇÃO DA PÁGINA (DOM CARREGADO)
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    fetchCartStatus();
});