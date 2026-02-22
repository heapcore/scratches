from datetime import datetime


class User:
    def __init__(self, name):
        self.name = name


class Message:
    def __init__(self, text):
        self.text = text
        print(text)


class Item:
    def __init__(self, name, warehouse_count):
        self.name = name
        self.warehouse_count = warehouse_count


class Cart:
    def __init__(self):
        self.created = datetime.now()
        self.items = []


class Order:
    PICKUP = "P"
    ONLINE = "O"
    PAYMENT_TYPE = (PICKUP, ONLINE)

    def __init__(self, items, payment_type, paid=False, payment_date=None):
        self.created = datetime.today()
        if isinstance(items, list):
            self.items = items
        else:
            self.items = []
        self.payment_type = payment_type
        self.paid = paid
        self.payment_date = payment_date
        self.cancelled = False

    @classmethod
    def fromcart(cls, cart, payment_type, paid=False, payment_date=None):
        return cls(cart.items, payment_type, paid)

    def pay(self):
        self.payment_date = datetime.now()
        self.paid = True


class StoreSession:
    def __init__(self, items, user):
        self.items = []
        for k, v in items.items():
            self.items.append(Item(name=k, warehouse_count=v))
        self.order = None
        self.cart = Cart()
        self.user = user

    def item_from_name(self, item_name):
        for item in self.items:
            if item.name == item_name:
                return item

    def process_payment(self):
        order = self.order
        items = order.items

        order.pay()
        items_unavailable = []
        for item in items:
            if item.warehouse_count <= 0:
                items_unavailable.append(item)
        if not items_unavailable:
            for item in items:
                item.warehouse_count -= 1
            Message("Your order is ready!")
        else:
            Message(
                "These items is currently unavailable: {}. Your order is cancelled!".format(
                    ", ".join(item.name for item in items_unavailable)
                )
            )
            order.cancelled = True

    def add_cart_item(self, item_name):
        cart_items = self.cart.items
        item = self.item_from_name(item_name)
        if item not in cart_items:
            cart_items.append(item)

    def delete_cart_item(self, item_name):
        cart_items = self.cart.items
        item = self.item_from_name(item_name)
        if item in cart_items:
            cart_items.remove(item)

    def create_order(self, payment_type):
        self.order = Order.fromcart(self.cart, payment_type)

    def pickup_order(self):
        order = self.order
        if order.payment_type == Order.ONLINE and order.paid == False:
            Message("Your order is not paid and will be cancelled!")
            order.cancelled = True


if __name__ == "__main__":
    print("test item adding in cart")
    s = StoreSession(
        items={"iphone": 2, "apple_watch": 1, "mi_band": 5}, user=User("Rahul")
    )
    s.add_cart_item("apple_watch")
    apple_watch = s.item_from_name("apple_watch")
    print(apple_watch in s.cart.items)

    print("test item deleting in cart")
    s.add_cart_item("iphone")
    s.add_cart_item("mi_band")
    s.delete_cart_item("apple_watch")
    print(all([apple_watch not in s.cart.items, len(s.cart.items) == 2]))

    print("check process payment")
    s.create_order(payment_type=Order.PICKUP)
    s.process_payment()
    s.pickup_order()
    mi_band = s.item_from_name("mi_band")
    print(
        all(
            [
                mi_band.warehouse_count == 4,
                s.order.paid == True,
                s.order.cancelled == False,
            ]
        )
    )

    print("check process payment: don't paid online")
    s = StoreSession(
        items={"iphone": 2, "apple_watch": 1, "mi_band": 5}, user=User("Ivan")
    )
    s.add_cart_item("apple_watch")
    s.create_order(payment_type=Order.ONLINE)
    s.process_payment()
    s.order.paid = False
    s.pickup_order()
    print(s.order.cancelled == True)

    print("check process payment: no item in warehouse")
    s = StoreSession(items={"iphone": 0, "mi_band": 5}, user=User("Ivan"))
    s.add_cart_item("iphone")
    s.create_order(payment_type=Order.ONLINE)
    s.process_payment()
    print(s.order.cancelled == True)
