from enum import Enum


class Side(Enum):
    BUY = ["buy", 1]
    SELL = ["sell", -1]


class OrderStatus(Enum):
    PENDING = "PENDING"
    CANCELED = "CANCELED"
    FILLED = "FILLED"


class Order:
    def __init__(self, stock: str, side: Side, price: float, size: int, time: int):
        self._id = None
        self._t = time
        self._stock = stock
        self._side = side
        self._price = price
        self._size = size
        self.status = OrderStatus.PENDING

    def describe(self):
        return "Order: ID:{} Stock:{} Side:{} Price:{} Size:{} Time:{} Status:{}".format(
            self._id,
            self._stock,
            self._side,
            self._price,
            self._size,
            self._t,
            self._status,
        )

    @property
    def id(self):
        return self._id

    @property
    def t(self):
        return self._t

    @property
    def stock(self):
        return self._stock

    @property
    def side(self):
        return self._side

    @property
    def price(self):
        return self._price

    @property
    def size(self):
        return self._size

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if isinstance(status, OrderStatus):
            self._status = status
        else:
            raise TypeError("Order status must be OrderStatus Enum")

    def set_id(self, id):
        self._id = id

    def set_price(self, price):
        self._price = price

    def set_remaining_size(self, volume):
        self._size += volume

    def set_filled(self):
        self._size = 0
        self._status = OrderStatus.FILLED

    def check_filled(self):
        if self._size == 0:
            self._status = OrderStatus.FILLED
            return True
        else:
            return False


class Trade:
    def __init__(
        self,
        id: int,
        stock: str,
        side: Side,
        price: float,
        size: int,
        time: int,
        order_index: int,
    ):
        self._id = id
        self._entry_t = time
        self._stock = stock
        self._side = side
        self._entry_price = price
        self._size = size  # Positive for buy, negative for sell
        self._trade_order = order_index

    def describe(self):
        return "Trade: {} {} {} {} {} {}".format(
            self._id,
            self._stock,
            self._side,
            self._size,
            self._entry_price,
            self._entry_t,
        )

    @property
    def id(self):
        return self._id

    @property
    def entry_t(self):
        return self._entry_t

    @property
    def stock(self):
        return self._stock

    @property
    def side(self):
        return self._side

    @property
    def entry_price(self):
        return self._entry_price

    @property
    def size(self):
        return self._size

    @property
    def trade_order(self):
        return self._trade_order

    def set_id(self, id):
        self._id = id

    def set_trade_order(self, order_index):
        self._trade_order = order_index


class StockData:
    def __init__(self, max_length=105):
        self.lob_deque = deque(maxlen=max_length)

    def update(self, lob_data):
        self.lob_deque.append(lob_data)
        # Additional processing can be added here
