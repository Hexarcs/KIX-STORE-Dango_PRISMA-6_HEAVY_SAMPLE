class KixCart:

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('kix_cart')
        if not cart:
            cart = self.session['kix_cart'] = {}
        self.cart = cart

    def add(self, product_id, name, price_sats, quantity=1):
        product_id = str(product_id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'name': name,
                'price_sats': int(price_sats),
                'quantity': 0,
            }
        self.cart[product_id]['quantity'] += int(quantity)
        self.save()

    def remove(self, product_id, quantity=1):
        product_id = str(product_id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] -= int(quantity)

            if self.cart[product_id]['quantity'] <= 0:
                del self.cart[product_id]

            self.save()

    def clear(self):
        self.session['kix_cart'] = {}
        self.save()

    def get_total_sats(self):
        return sum(
            item['price_sats'] * item['quantity'] for item in self.cart.values()
        )

    def get_total_items(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_items(self):
        """Retorna uma lista estruturada de itens com o subtotal de cada produto."""
        items = []
        for product_id, item in self.cart.items():
            items.append({
                'product_id': product_id,
                'name': item['name'],
                'price_sats': item['price_sats'],
                'quantity': item['quantity'],
                'subtotal_sats': item['price_sats'] * item['quantity'],
            })
        return items

    def get_summary(self):
        """Retorna o resumo completo do carrinho (Ideal para respostas JSON via API/AJAX)."""
        return {
            'items': self.get_items(),
            'total_items': self.get_total_items(),
            'total_sats': self.get_total_sats(),
        }

    def __iter__(self):
        """Permite iterar sobre os itens direto nos templates do Django com {% for item in cart %}"""
        for item in self.get_items():
            yield item

    def save(self):
        self.session.modified = True