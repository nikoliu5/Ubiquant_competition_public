from trade_mgmt import Order, Trade, OrderStatus, Side
from data_manager import DataManager
from position_manager import PositionManager
from interface import InterfaceClass
import pandas as pd


class Broker:
    def __init__(
        self, stock_list: list, api, token, data_manager: DataManager, time_info
    ):
        self._cash = 0
        self._tot_bp = 0
        self._ind_bp = 0
        self._my_bp = 0
        # TODO: Update positions
        self._tot_positions = 0
        self._init_positions = 0
        self._my_positions = 0
        self._stock_list = stock_list
        self._stock_trade_list = []
        self._active_orders = defaultdict(Order)
        self._closed_orders = defaultdict(Order)
        self._trade_list = defaultdict(Trade)
        self._data_manager = data_manager
        # Initialize all position managers
        self._pos_manager = defaultdict(PositionManager)
        for stock in self._stock_list:
            self._pos_manager[stock] = PositionManager(stock, data_manager)
        self._api = api
        self._token = token
        self._actual_pnl = 0
        self._actual_sharpe = 0
        self._score = 0
        self._time_info = time_info

    @property
    def cash(self):
        return self._cash

    @property
    def stock_list(self):
        return self._stock_list

    @property
    def active_order_list(self):
        return self._active_orders

    @property
    def closed_order_list(self):
        return self._closed_orders

    @property
    def trade_list(self):
        return self._trade_list

    @property
    def pos_manager(self):
        return self._pos_manager

    @property
    def actual_pnl(self):
        return self._actual_pnl

    @property
    def time_info(self):
        return self._time_info

    def set_stock_trade_list(self, stock_trade_list):
        self._stock_trade_list = stock_trade_list

    def get_stats(self):
        stats = f"<Broker: Current Cash:{self._cash:.2f}, Total Positions:{self._tot_positions:.2f}, My Positions:{self._my_positions:.2f}, Init Positions:{self._init_positions:.2f}, My PNL:{self._actual_pnl:.2f}>, My Sharpe:{self._actual_sharpe:.2f}>, My score:{self._score:.2f}>"
        logger.info(stats)
        return

    def init_broker(self):
        response = self._api.sendGetUserInfo(self._token)
        if response["status"] == "Success":
            logger.debug(f"Initializing Broker ------------------------")

            # Init positions
            self._cash = float(response["remain_funds"])
            self._tot_positions = response["total_position"]
            self._tot_bp = self._cash + self._tot_positions
            self._ind_bp = round(self._tot_bp / len(self._stock_trade_list))

            # Init Stats
            self._actual_pnl = response["pnl"]
            self._actual_sharpe = response["sharpe"]
            # self._score = response["score"]

            init_pos_path = "/root/init_positions/"
            if self._cash == 1000000:
                # Init df
                init_positions_res = response["rows"]
                init_pos_df = pd.DataFrame(init_positions_res)
                init_pos_df.to_csv(
                    init_pos_path + f"{self._time_info[1]}-{self._time_info[0]}.csv"
                )
                init_pos_df.set_index("instrument_name", inplace=True)
                self.init_pos_manager(init_pos_df)
                logger.info(
                    f"Clean Broker Init, saving init positions for Day {self._time_info[1]}"
                )
            else:
                logger.warning(
                    f"Broker Init Warning!!! Cash not 1000000, but {self._cash}"
                )
                try:
                    init_pos_df = pd.read_csv(
                        init_pos_path + f"{self._time_info[1]}-{self._time_info[0]}.csv"
                    )
                    init_pos_df.set_index("instrument_name", inplace=True)
                    self.init_pos_manager(init_pos_df)
                except FileNotFoundError:
                    logger.error(
                        f"Broker Init Error!!! No init positions for Day {self._time_info[1]}"
                    )
        else:
            logger.error(f"Broker Initialization Error: {response['status']}")

    def init_pos_manager(self, pos_df: pd.DataFrame):
        for stock_name in self._stock_list:
            try:
                stock_info = pos_df.loc[stock_name]
            except KeyError:
                logger.error(f"Could not retrieve init position for {stock_name} !!!!!")
                continue
            self._pos_manager[stock_name].set_init_size(stock_info["share_holding"])
            self._pos_manager[stock_name].set_init_position(stock_info["position"])
            self._pos_manager[stock_name].set_init_pnl(stock_info["pnl"])
        for stock_name in self._stock_trade_list:
            self._pos_manager[stock_name].set_init_bp(self._ind_bp)

    def calibrate_broker(self):
        response = self._api.sendGetUserInfo(self._token)
        if response["status"] == "Success":
            # logger.debug(f"Calibrate Broker ------------------")
            self._cash = float(response["remain_funds"])
            self._tot_positions = response["total_position"]
            self.update_pnl_all()
            if abs(self._actual_pnl - response["pnl"]) > 50:
                logger.warning(f"Actual PNL not match with Broker PNL")
                self._actual_pnl = response["pnl"]
            self._actual_sharpe = response["sharpe"]
            # self._score = response["score"]
            positions_info = response["rows"]
            self.calibrate_pos_manager(positions_info)
        else:
            logger.error(f"Broker Calibration Error: {response['status']}")

    def clean_init_positions(self):
        init_pos_path = "/root/init_positions/"
        file_path = init_pos_path + f"{self._time_info[1]}-{self._time_info[0]}.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Clean Init Positions for Day {self._time_info[1]}")
        else:
            logger.error(f"File {file_path} does not exist")

    def get_position(self, stock):
        return self._pos_manager[stock].position

    def update_pnl_all(self):
        self._actual_pnl = 0
        for stock in self._stock_list:
            self._pos_manager[stock].update_pnl()
            self._actual_pnl += self._pos_manager[stock].tot_pnl

    def get_pos_manager_info(self):
        for stock in self._stock_trade_list:
            self._pos_manager[stock].describe()

    def update_bp(self, new_bp):
        self._tot_bp = new_bp
        self._ind_bp = self._tot_bp / 10

    def calibrate_pos_manager(self, pos_info):
        for stock_info in pos_info:
            stock_name = stock_info["instrument_name"]
            self._pos_manager[stock_name].calibrate(
                stock_info["share_holding"], stock_info["position"], stock_info["pnl"]
            )
            self._pos_manager[stock_name].update_remain_bp()

    def risk_management_all(self):
        for stock in self._stock_list:
            self._pos_manager[stock].update_pnl()
            stock_unrealized_pnl = self._pos_manager[stock].unrealized_pnl
            stock_pos = self._pos_manager[stock].position
            if stock_unrealized_pnl > 0:
                continue
            loss_ratio = (-stock_unrealized_pnl) / stock_pos
            if stock_unrealized_pnl < 0 and loss_ratio > 0.05:
                self.neutralize_stock(stock, "best")
                logger.debug(
                    f"Risk Management Triggered!!! Unrealized PNL is {stock_unrealized_pnl} and Position is {stock_pos} and Loss Ratio is {loss_ratio}. Neutralize {stock} Position: {stock_pos} using Best Order"
                )

    # Order Submission System
    def custom_round(self, pos_value):
        return round(pos_value / 100) * 100

    def neutralize_all(self, order_type="second_best", n_th=3):
        logger.debug(f"Neutralize all positions with {order_type} Type")
        for stock in self._stock_list:
            self.neutralize_stock(stock, order_type, n_th)

    def neutralize_stock(self, stock, order_type="second_best", n_th=3, ratio=1):
        curr_time = ConvertToSimTime_us(*self._time_info)
        logger.debug(f"Neutralize all positions for {stock} with {order_type} Type")
        stock_pos = self._pos_manager[stock].position * ratio
        stock_pos = self.custom_round(stock_pos)
        if order_type == "market":
            if stock_pos > 0:
                self.submit_market_order(stock, Side.SELL, stock_pos, curr_time)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using Market Order"
                )
            elif stock_pos < 0:
                self.submit_market_order(stock, Side.BUY, -stock_pos, curr_time)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using Market Order"
                )
            else:
                pass
        elif order_type == "best":
            if stock_pos > 0:
                self.submit_best_order(stock, Side.SELL, stock_pos, curr_time)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using Best Order"
                )
            elif stock_pos < 0:
                self.submit_best_order(stock, Side.BUY, -stock_pos, curr_time)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using Best Order"
                )
            else:
                pass
        elif order_type == "second_best":
            if stock_pos > 0:
                self.submit_n_best_order(stock, Side.SELL, stock_pos, curr_time, 2)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using Second Best Order"
                )
            elif stock_pos < 0:
                self.submit_n_best_order(stock, Side.BUY, -stock_pos, curr_time, 2)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using Second Best Order"
                )
            else:
                pass
        elif order_type == "n_best":
            if stock_pos > 0:
                self.submit_n_best_order(stock, Side.SELL, stock_pos, curr_time, n_th)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using {n_th} Best Order"
                )
            elif stock_pos < 0:
                self.submit_n_best_order(stock, Side.BUY, -stock_pos, curr_time, n_th)
                logger.debug(
                    f"Neutralize {stock} Position: {stock_pos} using {n_th} Best Order"
                )
            else:
                pass

    def all_in_stock(self, stock, side: Side, ratio, order_type="second_best", n_th=2):
        curr_time = ConvertToSimTime_us(*self._time_info)
        logger.debug(f"All in positions for {stock} using {order_type} Type")
        stock_mid = self._pos_manager[stock]._last_mid_px
        if side == Side.BUY:
            remain_bp = self._pos_manager[stock].long_remain_bp
        elif side == Side.SELL:
            remain_bp = self._pos_manager[stock].short_remain_bp
        else:
            remain_bp = 0
        possible_pos = np.floor(remain_bp / stock_mid) * ratio
        possible_pos = self.custom_round(possible_pos) - 100
        if possible_pos < 100:
            logger.debug(f"Not enough cash/bp for adding position for {stock}")
            return
        if order_type == "market":
            self.submit_market_order(stock, side, possible_pos, curr_time)
            logger.debug(f"All in {stock} Position using Market Order: {possible_pos}")
        elif order_type == "best":
            self.submit_best_order(stock, side, possible_pos, curr_time)
            logger.debug(f"All in {stock} Position using Best Order: {possible_pos}")
        elif order_type == "second_best":
            self.submit_second_best_order(stock, side, possible_pos, curr_time)
            logger.debug(
                f"All in {stock} Position using Second Best Order: {possible_pos}"
            )
        elif order_type == "n_best":
            self.submit_n_best_order(stock, side, possible_pos, curr_time, n_th)
            logger.debug(
                f"All in {stock} Position using {n_th} Best Order: {possible_pos}"
            )
        elif order_type == "fill_or_kill":
            self.submit_fill_or_kill(stock, side, possible_pos, curr_time)
            logger.debug(
                f"All in {stock} Position using Fill or Kill Order: {possible_pos}"
            )
        elif order_type == "ladder":
            order_1 = self.custom_round(possible_pos * 0.2)
            order_2 = self.custom_round(possible_pos * 0.4)
            order_3 = self.custom_round(possible_pos * 0.4)
            order_4 = self.custom_round(possible_pos * 0.2)
            if order_1 >= 100:
                self.submit_best_order(stock, side, order_1, curr_time)
            if order_2 >= 100:
                self.submit_second_best_order(stock, side, order_2, curr_time)
            if order_3 >= 100:
                self.submit_n_best_order(stock, side, order_3, curr_time, 3)
            if order_4 >= 100:
                self.submit_n_best_order(stock, side, order_4, curr_time, 4)
        elif order_type == "short":
            possible_pos = self._pos_manager[stock].net_position - 100
            self.submit_best_order(stock, side, possible_pos, curr_time)
            logger.debug(
                f"All in Short {stock} Position using Second Best Order: {possible_pos}"
            )

    def submit_market_order(self, stock: str, side: Side, size: int, time: int):
        # Ensure price is right
        if side == Side.BUY:
            price = self._data_manager.get_best_ask(stock)
        elif side == Side.SELL:
            if self._pos_manager[stock].net_position < size:
                if self._pos_manager[stock].net_position == 0:
                    logger.debug(f"Position already 0 for {stock}")
                    return
                else:
                    logger.debug(
                        f"Position not enough to sell {stock}, only sell {self._pos_manager[stock].net_position}"
                    )
                    size = self._pos_manager[stock].net_position
            price = self._data_manager.get_best_bid(stock)
        else:
            raise TypeError("Side must be Side Enum")
        order_price = round(float(price), 2)
        response = self._api.sendOrder(
            self._token, stock, time, side.value[0], order_price, size
        )
        if response["status"] == "Success":
            order = Order(stock, side, price, size, time)
            order_id = response["index"]
            order.set_id(order_id)
            self._active_orders[order_id] = order
            logger.debug("Submit Market Order: {}".format(order.describe()))
        else:
            logger.debug("Submit Market Order Error: {}".format(response["status"]))

    def submit_best_order(self, stock: str, side: Side, size: int, time: int):
        # Ensure price is right
        if side == Side.BUY:
            price = self._data_manager.get_best_bid(stock) - 0.01
        elif side == Side.SELL:
            if self._pos_manager[stock].net_position < size:
                if self._pos_manager[stock].net_position == 0:
                    logger.debug(f"Position already 0 for {stock}")
                    return
                else:
                    logger.debug(
                        f"Position not enough to sell {stock}, only sell {self._pos_manager[stock].net_position}"
                    )
                    size = self._pos_manager[stock].net_position
            price = self._data_manager.get_best_ask(stock) + 0.01
        else:
            raise TypeError("Side must be Side Enum")
        order_price = round(float(price), 2)
        response = self._api.sendOrder(
            self._token, stock, time, side.value[0], order_price, size
        )
        if response["status"] == "Success":
            order = Order(stock, side, price, size, time)
            order_id = response["index"]
            order.set_id(order_id)
            self._active_orders[order_id] = order
            logger.debug("Submit Best Order: {}".format(order.describe()))
        else:
            logger.debug("Submit Best Order Error: {}".format(response["status"]))

    def submit_second_best_order(self, stock: str, side: Side, size: int, time: int):
        # Ensure price is right
        if side == Side.BUY:
            price = self._data_manager.get_second_best_bid(stock)
        elif side == Side.SELL:
            if self._pos_manager[stock].net_position < size:
                if self._pos_manager[stock].net_position == 0:
                    logger.debug(f"Position already 0 for {stock}")
                    return
                else:
                    logger.debug(
                        f"Position not enough to sell {stock}, only sell {self._pos_manager[stock].net_position}"
                    )
                    size = self._pos_manager[stock].net_position
            price = self._data_manager.get_second_best_ask(stock)
        else:
            raise TypeError("Side must be Side Enum")
        order_price = round(float(price), 2)
        response = self._api.sendOrder(
            self._token, stock, time, side.value[0], order_price, size
        )
        if response["status"] == "Success":
            order = Order(stock, side, price, size, time)
            order_id = response["index"]
            order.set_id(order_id)
            self._active_orders[order_id] = order
            logger.debug("Submit Second Best Order: {}".format(order.describe()))
        else:
            logger.debug(
                "Submit Second Best Order Error: {}".format(response["status"])
            )

    def submit_third_best_order(self, stock: str, side: Side, size: int, time: int):
        # Ensure price is right
        if side == Side.BUY:
            price = self._data_manager.get_n_best_bid(stock, 3)
        elif side == Side.SELL:
            if self._pos_manager[stock].net_position < size:
                if self._pos_manager[stock].net_position == 0:
                    logger.debug(f"Position already 0 for {stock}")
                    return
                else:
                    logger.debug(
                        f"Position not enough to sell {stock}, only sell {self._pos_manager[stock].net_position}"
                    )
                    size = self._pos_manager[stock].net_position
            price = self._data_manager.get_n_best_ask(stock, 3)
        else:
            raise TypeError("Side must be Side Enum")
        order_price = round(float(price), 2)
        response = self._api.sendOrder(
            self._token, stock, time, side.value[0], order_price, size
        )
        if response["status"] == "Success":
            order = Order(stock, side, price, size, time)
            order_id = response["index"]
            order.set_id(order_id)
            self._active_orders[order_id] = order
            logger.debug("Submit Third Best Order: {}".format(order.describe()))
        else:
            logger.debug("Submit Third Best Order Error: {}".format(response["status"]))

    def submit_n_best_order(
        self, stock: str, side: Side, size: int, time: int, n_th: int
    ):
        # Ensure price is right
        if side == Side.BUY:
            price = self._data_manager.get_n_best_bid(stock, n_th)
        elif side == Side.SELL:
            if self._pos_manager[stock].net_position < size:
                if self._pos_manager[stock].net_position == 0:
                    logger.debug(f"Position already 0 for {stock}")
                    return
                else:
                    logger.debug(
                        f"Position not enough to sell {stock}, only sell {self._pos_manager[stock].net_position}"
                    )
                    size = self._pos_manager[stock].net_position
            price = self._data_manager.get_n_best_ask(stock, n_th)
        else:
            raise TypeError("Side must be Side Enum")
        order_price = round(float(price), 2)
        response = self._api.sendOrder(
            self._token, stock, time, side.value[0], order_price, size
        )
        if response["status"] == "Success":
            order = Order(stock, side, price, size, time)
            order_id = response["index"]
            order.set_id(order_id)
            self._active_orders[order_id] = order
            logger.debug(f"Submit {n_th} Best Order: {order.describe()}")
        else:
            logger.debug(f"Submit {n_th} Best Order Error: {response['status']}")

    def submit_fill_or_kill(self, stock: str, side: Side, size: int, time: int):
        # Ensure price is right
        if side == Side.BUY:
            price = self._data_manager.get_best_bid(stock)
        elif side == Side.SELL:
            if self._pos_manager[stock].net_position < size:
                if self._pos_manager[stock].net_position == 0:
                    logger.debug(f"Position already 0 for {stock}")
                    return
                else:
                    logger.debug(
                        f"Position not enough to sell {stock}, only sell {self._pos_manager[stock].net_position}"
                    )
                    size = self._pos_manager[stock].net_position
            price = self._data_manager.get_best_ask(stock)
        else:
            raise TypeError("Side must be Side Enum")
        order_price = round(float(price), 2)
        response = self._api.sendOrder(
            self._token, stock, time, side.value[0], order_price, size
        )
        if response["status"] == "Success":
            order = Order(stock, side, price, size, time)
            order_id = response["index"]
            order.set_id(order_id)
            self.cancel_order(order)
            self._closed_orders[order_id] = order
            logger.debug("Submit Fill or Kill Order: {}".format(order.describe()))
        else:
            logger.debug(
                "Submit Fill or Kill Order Error: {}".format(response["status"])
            )

    def submit_order(self, stock: str, side: Side, price: float, size: int, time: int):
        # Ensure price is right
        order_price = round(float(price), 2)
        response = self._api.sendOrder(
            self._token, stock, time, side.value[0], order_price, size
        )
        if response["status"] == "Success":
            order = Order(stock, side, price, size, time)
            order_id = response["index"]
            order.set_id(order_id)
            self._active_orders[order_id] = order
            logger.debug("Submit Order: {}".format(order.describe()))
        else:
            logger.debug("Submit Order Error: {}".format(response["status"]))

    def cancel_active_order_stock(self, stock):
        order_ids = []
        for order in self._active_orders.values():
            if order.stock == stock:
                order_ids.append(order.id)

        time = ConvertToSimTime_us(*self._time_info)
        for order_id in order_ids:
            response = self._api.sendCancel(self._token, stock, time, order_id)
            if response["status"] == "Success":
                logger.debug(
                    f"Cancel Order: Instrument:{stock} Order_index: {order_id}"
                )
            else:
                logger.debug(f"Cancel Order Error: {response['status']}")

            self._closed_orders[order_id] = self._active_orders[order_id]
            del self._active_orders[order_id]

    def cancel_order(self, order_info):
        time = ConvertToSimTime_us(*self._time_info)
        response = self._api.sendCancel(
            self._token, order_info.stock, time, order_info.id
        )
        if response["status"] == "Success":
            logger.debug(f"Cancel Order: {order_info.id}")
        else:
            logger.debug(f"Cancel Order Error: {response['status']}")
        self._closed_orders[order_info.id] = self._active_orders[order_info.id]
        del self._active_orders[order_info.id]

    # Trade Info System
    async def get_trade_info(self):
        # Switch Between trading and stock list
        tasks = [self.fetch_trade_data(stock) for stock in self._stock_trade_list]
        await asyncio.gather(*tasks)

    async def fetch_trade_data(self, stock):
        try:
            response = await self._api.sendGetTradeAsync(self._token, stock)
            if response["status"] == "Success":
                # logger.debug(f"Get Stock Trade info: {stock} Trade List: {response}")
                if len(response["trade_list"]) != 0:
                    # logger.debug(f"Successful Get Stock Trade info: {stock}")
                    for trade_info in response["trade_list"]:
                        trade_index = trade_info["trade_index"]
                        if trade_index in self._trade_list:
                            continue
                        # Get Matched Order and info
                        order_idx = trade_info["order_index"]
                        if order_idx in self._closed_orders:
                            matched_order = self._closed_orders[order_idx]
                            trade_side = self._closed_orders[order_idx].side
                        elif order_idx in self._active_orders:
                            matched_order = self._active_orders[order_idx]
                            trade_side = self._active_orders[order_idx].side
                        else:
                            trade_side = Side.BUY
                            logger.debug(
                                f"Does not find the matched order for {order_idx}"
                            )
                            for key, item in self._active_orders.items():
                                print("Active order key:", key)

                        trade_volume = trade_info["trade_volume"] * trade_side.value[1]
                        # Create Trade Object
                        trade = Trade(
                            trade_index,
                            stock,
                            trade_side,
                            trade_info["trade_price"],
                            trade_volume,
                            trade_info["trade_time"],
                            order_idx,
                        )
                        self._trade_list[trade_index] = trade
                        # logger.debug(f"Fetch Stock Data {stock} 3")
                        # Update Position Manager
                        self._pos_manager[stock].add_trade(trade)
                        matched_order.set_remaining_size(trade_volume)
                        if trade_info["remain_volume"] == 0:
                            matched_order.set_filled()
                            self._closed_orders[order_idx] = matched_order
                            del self._active_orders[order_idx]

            else:
                logger.debug(f"Get Stock Trade info Error: {response['status']}")
        except Exception as e:
            logger.error(f"Error fetching trade data for {stock}: {e}")


def ConvertToSimTime_us(start_time, time_ratio, day, running_time):
    return (time.time() - start_time - (day - 1) * running_time) * time_ratio
