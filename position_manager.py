from trade_mgmt import Trade
from data_manager import DataManager

# Position Manager for individual stock
class PositionManager:
    def __init__(self, stock: str, data_manager):
        self._stock = stock
        self._init_size = 0
        self._init_position = 0
        self._long_position_size = 0
        self._short_position_size = 0
        self._long_avg_price = 0
        self._short_avg_price = 0
        self._realized_pnl = 0
        self._unrealized_pnl = 0
        self._trade_list = []
        self._tot_pnl = 0
        self._tot_pnl_pct = 0
        self._trade_num = 0
        self._data_manager = data_manager
        self._last_mid_px = 0
        self._stock_bp = 0
        self._long_remain_bp = 0
        self._short_remain_bp = 0
        self._my_position = 0

    def describe(self):
        logger.debug(
            f"PositionManager for Stock:{self._stock} My Total Position: {self._long_position_size - self._short_position_size}, My Long Position: {self._long_position_size}, My Short Position: {self._short_position_size}, My Total PNL: {self._tot_pnl}"
        )

    @property
    def stock(self):
        return self._stock

    @property
    def trade_list(self):
        return self._trade_list

    @property
    def trade_num(self):
        return self._trade_num

    @property
    def stock_bp(self):
        return self._stock_bp

    @property
    def long_remain_bp(self):
        return self._long_remain_bp

    @property
    def short_remain_bp(self):
        return self._short_remain_bp

    @property
    def last_mid_px(self):
        return self._last_mid_px

    @property
    def init_size(self):
        return self._init_size

    @property
    def tot_pnl(self):
        return self._tot_pnl

    @property
    def long_position_size(self):
        return self._long_position_size

    @property
    def short_position_size(self):
        return self._short_position_size

    @property
    def long_avg_price(self):
        return self._long_avg_price

    @property
    def short_avg_price(self):
        return self._short_avg_price

    @property
    def position(self):
        self.calc_my_position()
        return self._my_position

    @property
    def net_position(self):
        self.calc_my_position()
        return self._my_position + self._init_size

    @property
    def unrealized_pnl(self):
        return self._unrealized_pnl

    def set_init_size(self, size):
        self._init_size = size

    def set_init_position(self, position_val):
        self._init_position = position_val

    def get_init_position(self):
        self._init_position = self._init_size * self._last_mid_px
        return self._init_position

    def set_init_pnl(self, pnl_val):
        self._pnl = pnl_val

    def set_init_bp(self, bp):
        self._stock_bp = int(bp - self._init_position) - 1000
        logger.debug(f"Set Init BP for {self._stock}: {self._stock_bp}")

    def calc_my_position(self):
        self._my_position = self._long_position_size - self._short_position_size

    def add_trade(self, trade: Trade):
        self._trade_list.append(trade)
        self._trade_num += 1
        self.calc_my_position()
        # logger.debug(f"Add Trade for {self._stock}: {trade.describe()}")
        if trade.size > 0:
            # logger.debug(f"Trade Size: {trade.size} is positive, update long position")
            if self._my_position >= 0:
                self.update_position("long", trade)
            else:
                self.close_update_position("short", trade)
        elif trade.size < 0:
            # logger.debug(f"Trade Size: {trade.size} is negative, update short position")
            if self._my_position <= 0:
                self.update_position("short", trade)
            else:
                self.close_update_position("long", trade)
        else:
            pass

    def update_position(self, position_type, trade: Trade):
        if position_type == "long":
            # logger.debug(f"Update Long Position for {self._stock} with Trade: {trade.describe()}")
            new_total_value = (
                self._long_avg_price * self._long_position_size
                + trade.entry_price * trade.size
            )
            self._long_position_size += trade.size
            if self._long_position_size != 0:
                self._long_avg_price = new_total_value / self._long_position_size
        elif position_type == "short":
            # logger.debug(f"Update Short Position for {self._stock} with Trade: {trade.describe()}")
            adjusted_trade_size = abs(trade.size)
            new_total_value = (
                self._short_avg_price * self._short_position_size
                + trade.entry_price * adjusted_trade_size
            )
            self._short_position_size += adjusted_trade_size
            if self._short_position_size != 0:
                self._short_avg_price = new_total_value / self._short_position_size
        else:
            logger.error(f"Invalid Position Type: {position_type}")

    def close_update_position(self, position_type, trade: Trade):

        adjusted_trade_size = abs(trade.size)
        closing_size = min(
            adjusted_trade_size,
            self._long_position_size
            if position_type == "long"
            else self._short_position_size,
        )
        remaining_size = adjusted_trade_size - closing_size

        # logger.debug(f"Close Update Position for {self._stock}")
        # logger.debug(f"Adjusted Trade Size: {adjusted_trade_size}")
        # logger.debug(f"Closing Size: {closing_size}")
        # logger.debug(f"Remaining Size: {remaining_size}")
        # logger.debug(f"Before Long Position size: {self._long_position_size}")
        # logger.debug(f"Before Short Position size: {self._short_position_size}")
        # Calculate realized PnL for the closing part
        if position_type == "long":
            closing_pnl = closing_size * (trade.entry_price - self._long_avg_price)
            self._long_position_size -= closing_size
        elif position_type == "short":
            closing_pnl = closing_size * (self._short_avg_price - trade.entry_price)
            self._short_position_size -= closing_size
        else:
            logger.error(f"Invalid Position Type: {position_type}")

        self._realized_pnl += closing_pnl

        # Handle remaining size of trade
        if remaining_size > 0:
            if position_type == "long":
                self._long_position_size += remaining_size
                new_total_value = (
                    self._long_avg_price * self._long_position_size
                    + trade.entry_price * remaining_size
                )
                self._long_avg_price = new_total_value / self._long_position_size
                # self._short_position_size = 0
            else:
                self._short_position_size += remaining_size
                new_total_value = (
                    self._short_avg_price * self._short_position_size
                    + trade.entry_price * remaining_size
                )
                self._short_avg_price = new_total_value / self._short_position_size
                # self._long_position_size = 0
        # logger.debug(f"After Long Position size: {self._long_position_size}")
        # logger.debug(f"After Short Position size: {self._short_position_size}")

    def update_unrealized_pnl(self):
        self._last_mid_px = self._data_manager.get_last_mid(self._stock)
        long_unrealized_pnl = self._long_position_size * (
            self._last_mid_px - self._long_avg_price
        )
        short_unrealized_pnl = self._short_position_size * (
            self._short_avg_price - self._last_mid_px
        )
        self._unrealized_pnl = long_unrealized_pnl + short_unrealized_pnl

    def update_pnl(self):
        self.update_unrealized_pnl()
        self._tot_pnl = self._realized_pnl + self._unrealized_pnl

    def remove_trade(self, trade: Trade):
        self._trade_list.remove(trade)

    def custom_round(self, pos_value):
        return round(pos_value / 100) * 100

    def calibrate(self, share_holding, total_value, pnl):
        share_holding = int(share_holding)
        total_value = float(total_value)
        pnl = float(pnl)
        self._last_mid_px = self._data_manager.get_last_mid(self._stock)

        tot_pos_size = (
            self._long_position_size - self._short_position_size + self._init_size
        )

        # Calibrate Position Size
        if tot_pos_size != share_holding:
            logger.debug(
                f"Position Manager for {self._stock} Calibrated.  Original Total Position:{tot_pos_size} Calibrated Total Position:{share_holding}"
            )
            my_pos_size = share_holding - self._init_size
            if my_pos_size > 0:
                self._long_position_size = my_pos_size
                self._short_position_size = 0
            elif my_pos_size < 0:
                self._long_position_size = 0
                self._short_position_size = abs(my_pos_size)

        # Calibrate Avg Price
        self._init_position = self._init_size * self._last_mid_px
        remaining_pos = total_value - self._init_position
        # logger.debug(f"{self._stock} Total Position:{total_value} Remaining Position: {remaining_pos}, Init Size for: {self._init_size}, Init Position: {self._init_position}")
        if abs(remaining_pos) < 500:
            remaining_pos = 0
            # logger.debug(f"Remaining Position for {self._stock} is too small, set to 0")
        if remaining_pos > 0:
            self._short_position_size = 0
            if self._long_position_size != 0:
                cal_avg_price = remaining_pos / self._long_position_size
                if round(cal_avg_price, 2) != round(self._long_avg_price, 2):
                    # logger.debug(f"Position Manager for {self._stock} Calibrated.  Original Long Avg Price:{self._long_avg_price} Calibrated Avg Price:{cal_avg_price}")
                    self._long_avg_price = cal_avg_price
            else:
                self._long_position_size = self.custom_round(
                    remaining_pos / self._last_mid_px
                )
                logger.warning(
                    f"Calibration Error: {self._stock} Remaining Position is {remaining_pos}, but long position size is 0, Calibrate Long Position Size to {self._long_position_size}"
                )

        elif remaining_pos < 0:
            self._long_position_size = 0
            if self._short_position_size != 0:
                cal_avg_price = abs(remaining_pos) / self._short_position_size
                if round(cal_avg_price, 2) != round(self._short_avg_price, 2):
                    # logger.debug(f"Position Manager for {self._stock} Calibrated.  Original Short Avg Price:{self._short_avg_price} Calibrated Avg Price:{cal_avg_price}")
                    self._short_avg_price = cal_avg_price
            else:
                self._short_position_size = self.custom_round(
                    abs(remaining_pos) / self._last_mid_px
                )
                logger.warning(
                    f"Calibration Error: {self._stock} Remaining Position is {remaining_pos}, but short position size is 0, Calibrate Short Position Size to {self._short_position_size}"
                )
        else:
            if self._long_position_size != 0 or self._short_position_size != 0:
                logger.warning(
                    f"Calibration Error: Remaining Position is 0, but long position size is {self._long_position_size}, short position size is {self._short_position_size}"
                )
            self._long_position_size = 0
            self._short_position_size = 0
            self._long_avg_price = 0
            self._short_avg_price = 0
        self.calc_my_position()

        self.update_pnl()
        # Calibrate PNL
        if abs(self._tot_pnl - pnl) > 5:
            # logger.debug(f"Position Manager for {self._stock} Calibrated. Calibrated Total PNL:{pnl} ----- Original Total PNL:{self._tot_pnl} Realized PNL:{self._realized_pnl} Unrealized PNL:{self._unrealized_pnl}, Long Position Size:{self._long_position_size} Long Avg Price:{self._long_avg_price} Short Position Size:{self._short_position_size} Short Avg Price:{self._short_avg_price}")
            self._tot_pnl = pnl
            self._realized_pnl = pnl - self._unrealized_pnl

    def update_remain_bp(self):
        long_pos_val = self._long_position_size * self._last_mid_px
        short_pos_val = self._short_position_size * self._last_mid_px
        self._long_remain_bp = int(self._stock_bp - long_pos_val + short_pos_val)
        self._short_remain_bp = int(self._stock_bp - short_pos_val + long_pos_val)
