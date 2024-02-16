from broker import Broker
from data_manager import DataManager
from trade_mgmt import Side


class Strategy:
    def __init__(self, stock_list, data_manager: DataManager, broker: Broker):
        self._data_manager = data_manager
        self._broker = broker
        self._stock_list = stock_list
        self._stock_trade_list = []
        self._pos_manager = self._broker._pos_manager
        self.placeholder_model = None
        self.models = defaultdict(lambda: self.placeholder_model)

        # Load a model for each stock, if available
        for stock in self._stock_list:
            # Default model path
            model_path = f"/root/model_high_mid/LightGBM_{stock}.joblib"
            try:
                self.models[stock] = joblib.load(model_path)
                self._stock_trade_list.append(stock)
            except FileNotFoundError:
                continue
        self.buy_signals = defaultdict(int)
        self.sell_signals = defaultdict(int)

    @property
    def stock_trade_list(self):
        return self._stock_trade_list

    def trade_decision_all(self):
        for stock in self._stock_trade_list:
            self.trade_decision_stock(stock)

    def trade_decision_stock(self, stock):
        if self.models[stock] is None:
            # logger.debug(f"No model for {stock}")
            return
        window = 100
        features = self._data_manager.get_model_data(stock, window)
        if features.empty:
            logger.debug(f"Not enough data for {stock}")
            return

        if isinstance(features, pd.Series):
            features = features.values.reshape(1, -1)
        elif isinstance(features, np.ndarray):
            features = features.reshape(1, -1)

        predict_prob = self.models[stock].predict_proba(features)
        logger.debug(f"Predict Prob for {stock}: {predict_prob}")
        prediction = np.where(
            predict_prob[0][1] > 0.75,
            1,
            np.where(predict_prob[0][1] < 0.25, 0, predict_prob[0][1]),
        )
        # prediction = np.where(predict_prob[0][1] > 0.5, 1, np.where(predict_prob[0][1] < 0.5, 0, predict_prob[0][1]))
        # logger.debug(f"Prediction for {stock}: {prediction}")

        if prediction == 1:
            logger.debug(f"Buy {stock} -------------------------")
            # self._broker.submit_best_order(stock, Side.BUY, 5000, t)
            self._broker.cancel_active_order_stock(stock)
            # self._broker.all_in_stock(stock, Side.SELL, 0.5, 'short')
            # self._broker.all_in_stock(stock, Side.BUY, 1, 'ladder')
            self._broker.all_in_stock(stock, Side.BUY, 0.25, "n_best", 2)

        elif prediction == 0:
            logger.debug(f"Sell {stock} -----------------------------")
            # self._broker.submit_market_order(stock, Side.SELL, 1000, t)
            self._broker.cancel_active_order_stock(stock)
            self._broker.neutralize_stock(stock, "n_best", 3, 0.5)
            # self._broker.all_in_stock(stock, Side.SELL, 0.5, 'short')
            # self._broker.all_in_stock(stock, Side.SELL, 0.5, 'n_best', 3)
        else:
            pass
            # logger.debug(f"Prediction for {stock} is {prediction}, do nothing")
