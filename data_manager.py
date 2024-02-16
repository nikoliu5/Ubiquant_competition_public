from trade_mgmt import StockData
import asyncio
import itertools
import pandas as pd
import numpy as np
from typing import List


class DataManager:
    def __init__(self, stock_list: List, api, token):
        self._stock_list = stock_list
        self._api = api
        self._token = token
        self._last_update_time = None
        # self._price_map = {}
        self._data_map = {stock: StockData() for stock in stock_list}

    async def update_lob(self):
        tasks = [self.fetch_stock_data(stock) for stock in self._stock_list]
        await asyncio.gather(*tasks)

    async def fetch_stock_data(self, stock):
        try:
            response = await self._api.sendGetLimitOrderBookAsync(self._token, stock)
            if response["status"] == "Success":
                lob_data = response["lob"]
                self._data_map[stock].update(
                    {
                        "last_price": lob_data["last_price"],
                        "trade_volume": lob_data["trade_volume"],
                        "trade_value": lob_data["trade_value"],
                        "askprice": lob_data["askprice"],
                        "askvolume": lob_data["askvolume"],
                        "bidprice": lob_data["bidprice"],
                        "bidvolume": lob_data["bidvolume"],
                    }
                )
                # logger.debug(f"Update LOB for {stock}")
            else:
                logger.debug(f"Update LOB Error: {response['status']}")
        except Exception as e:
            logger.error(f"Error updating LOB for {stock}: {e}")

    def get_last_price(self, stock):
        try:
            # Access the most recent data from the deque
            last_data = self._data_map[stock].lob_deque[-1]
            last_price = last_data["last_price"]
            # logger.debug(f"Get Last Price for {stock}: {last_price}")
            return last_price
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting last price for {stock}: {e}")

    def get_last_mid(self, stock):
        try:
            last_data = self._data_map[stock].lob_deque[-1]
            best_bid = float(last_data["bidprice"][0])
            best_ask = float(last_data["askprice"][0])
            last_mid = round((best_bid + best_ask) / 2, 3)
            return last_mid
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting last mid price for {stock}: {e}")

    def get_best_bid(self, stock):
        try:
            last_data = self._data_map[stock].lob_deque[-1]
            best_bid = float(last_data["bidprice"][0])
            logger.debug(f"Get Best Bid for {stock}: {best_bid}")
            return best_bid
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting best bid for {stock}: {e}")

    def get_best_ask(self, stock):
        try:
            last_data = self._data_map[stock].lob_deque[-1]
            best_ask = float(last_data["askprice"][0])
            # logger.debug(f"Get Best Ask for {stock}: {best_ask}")
            return best_ask
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting best ask for {stock}: {e}")

    def get_second_best_bid(self, stock):
        try:
            last_data = self._data_map[stock].lob_deque[-1]
            best_bid = float(last_data["bidprice"][1])
            # logger.debug(f"Get Best Bid for {stock}: {best_bid}")
            return best_bid
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting best bid for {stock}: {e}")

    def get_second_best_ask(self, stock):
        try:
            last_data = self._data_map[stock].lob_deque[-1]
            best_ask = float(last_data["askprice"][1])
            # logger.debug(f"Get Best Ask for {stock}: {best_ask}")
            return best_ask
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting best ask for {stock}: {e}")

    def get_n_best_bid(self, stock, n):
        try:
            last_data = self._data_map[stock].lob_deque[-1]
            best_bid = float(last_data["bidprice"][n - 1])
            # logger.debug(f"Get Best Bid for {stock}: {best_bid}")
            return best_bid
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting best bid {n} for {stock}: {e}")

    def get_n_best_ask(self, stock, n):
        try:
            last_data = self._data_map[stock].lob_deque[-1]
            best_ask = float(last_data["askprice"][n - 1])
            # logger.debug(f"Get Best Ask for {stock}: {best_ask}")
            return best_ask
        except IndexError:
            logger.error(f"No data available for {stock}")
        except Exception as e:
            logger.error(f"Error getting best ask {n} for {stock}: {e}")

    def get_window_data(self, stock, window=100):
        try:
            data = self._data_map[stock].lob_deque
            if len(data) >= window:
                # Use islice to get the last 'window' elements from the deque
                window_data = list(
                    itertools.islice(data, len(data) - window, len(data))
                )
                return window_data
            else:
                logger.warning(
                    f"Not enough data available for {stock}. Expected {window} data points, got {len(data)}"
                )
                return -1
        except IndexError:
            logger.error(f"No data available for {stock}")
            return -1
        except Exception as e:
            logger.error(f"Error getting window for {stock}: {e}")
            return -1

    def get_model_data(self, stock, window=100):
        window_data = self.get_window_data(stock, window)
        if window_data == -1:
            return pd.DataFrame()

        start_time = time.time()  # Start timing
        all_rows = []

        for lob_data in window_data:
            row = {
                "LastPrice": lob_data["last_price"],
                "TradeVolume": lob_data["trade_volume"],
                "TradeValue": lob_data["trade_value"],
            }
            for i in range(10):
                row[f"BidPrice{i+1}"] = (
                    lob_data["bidprice"][i] if i < len(lob_data["bidprice"]) else None
                )
                row[f"AskPrice{i+1}"] = (
                    lob_data["askprice"][i] if i < len(lob_data["askprice"]) else None
                )
                row[f"BidVolume{i+1}"] = (
                    lob_data["bidvolume"][i] if i < len(lob_data["bidvolume"]) else None
                )
                row[f"AskVolume{i+1}"] = (
                    lob_data["askvolume"][i] if i < len(lob_data["askvolume"]) else None
                )
            all_rows.append(row)

        df = pd.DataFrame(all_rows)

        feature_col = [
            "price_vs_mid",
            "spread",
            "positive_ratio",
            "avg_distance_diff",
            "amt_spread_tick",
            "amt_spread_tick4",
            "ask_dist",
            "bid_dist",
            "depth_price_range",
            "Vol_Imbalance",
            "bp_rank",
            "ap_rank",
            "price_impact",
            "depth_price_skew",
            "depth_price_kurt",
            "rolling_return",
            "quasi",
            "avg_spread",
            "avg_turnover",
            "avg_trade_volume",
            "volume_kurt",
            "volume_skew",
            "weighted_price_to_mid",
        ]

        df["MidPrice"] = (df["BidPrice1"] + df["AskPrice1"]) / 2
        df["W_Mid_Price"] = (
            df["BidPrice1"] * df["AskVolume1"] + df["AskPrice1"] * df["BidVolume1"]
        ) / (df["BidVolume1"] + df["AskVolume1"])
        df["Volume"] = df["TradeVolume"].diff()
        df["return"] = df["MidPrice"].pct_change()
        df["price_vs_mid"] = np.log(df["LastPrice"] / df["MidPrice"])
        df["spread"] = df["AskPrice1"] - df["BidPrice1"]
        df["pos_trades"] = (df["LastPrice"] >= df["AskPrice1"].shift(1)).astype(int)
        df["positive_ratio"] = df["pos_trades"].rolling(window).sum() / window
        df["avg_distance_diff"] = (df["BidPrice1"] - df["BidPrice10"]) - (
            df["AskPrice10"] - df["AskPrice1"]
        ) * 100

        df["w_bid_amt"] = sum(
            df[f"BidPrice{i}"] * df[f"BidVolume{i}"] * (1 - (i - 1) / 10)
            for i in range(1, 11)
        )
        df["w_ask_amt"] = sum(
            df[f"AskPrice{i}"] * df[f"AskVolume{i}"] * (1 - (i - 1) / 10)
            for i in range(1, 11)
        )
        df["amt_spread_tick"] = np.where(
            (df["w_bid_amt"] + df["w_ask_amt"]) > 0,
            (df["w_bid_amt"] - df["w_ask_amt"]) / (df["w_bid_amt"] + df["w_ask_amt"]),
            0,
        )

        df["w_bid_amt4"] = sum(
            df[f"BidPrice{i}"] * df[f"BidVolume{i}"] * (1 - (i - 1) / 4)
            for i in range(1, 5)
        )
        df["w_ask_amt4"] = sum(
            df[f"AskPrice{i}"] * df[f"AskVolume{i}"] * (1 - (i - 1) / 4)
            for i in range(1, 5)
        )
        df["amt_spread_tick4"] = np.where(
            (df["w_bid_amt4"] + df["w_ask_amt4"]) > 0,
            (df["w_bid_amt4"] - df["w_ask_amt4"])
            / (df["w_bid_amt4"] + df["w_ask_amt4"]),
            0,
        )

        df["tot_ask_amt"] = sum(
            df[f"AskPrice{i}"] * df[f"AskVolume{i}"] for i in range(1, 11)
        )
        df["tot_bid_amt"] = sum(
            df[f"BidPrice{i}"] * df[f"BidVolume{i}"] for i in range(1, 11)
        )

        # Vectorized total volumes
        df["total_bid_vol"] = df[[f"BidVolume{i}" for i in range(1, 11)]].sum(axis=1)
        df["total_ask_vol"] = df[[f"AskVolume{i}" for i in range(1, 11)]].sum(axis=1)

        # VWAP calculations using direct division
        df["ask_vwap"] = df["tot_ask_amt"] / df["total_ask_vol"]
        df["bid_vwap"] = df["tot_bid_amt"] / df["total_bid_vol"]

        # Distance from mid price with direct subtraction
        df["ask_dist"] = df["ask_vwap"] - df["MidPrice"]
        df["bid_dist"] = df["MidPrice"] - df["bid_vwap"]

        window_size = 60
        df["depth_price_range"] = (
            df["AskPrice1"].rolling(window_size).max()
            / df["AskPrice1"].rolling(window_size).min()
            - 1
        ).fillna(0)

        df["Bid_Volume_top4"] = (
            df["BidVolume1"] + df["BidVolume2"] + df["BidVolume3"] + df["BidVolume4"]
        )
        df["Ask_Volume_top4"] = (
            df["AskVolume1"] + df["AskVolume2"] + df["AskVolume3"] + df["AskVolume4"]
        )
        df["Vol_Imbalance"] = (df["Bid_Volume_top4"] - df["Ask_Volume_top4"]) / (
            df["Bid_Volume_top4"] + df["Ask_Volume_top4"]
        )

        df["bp_rank"] = (
            df["BidPrice1"].rolling(window_size).rank() / window_size * 2 - 1
        ).fillna(0)
        df["ap_rank"] = (
            df["AskPrice1"].rolling(window_size).rank() / window_size * 2 - 1
        ).fillna(0)

        n = 10
        aps = sum(df[f"AskPrice{i}"] * df[f"AskVolume{i}"] for i in range(1, n + 1))
        bps = sum(df[f"BidPrice{i}"] * df[f"BidVolume{i}"] for i in range(1, n + 1))
        avs = sum(df[f"AskVolume{i}"] for i in range(1, n + 1))
        bvs = sum(df[f"BidVolume{i}"] for i in range(1, n + 1))

        aps /= avs
        bps /= bvs
        df["price_impact"] = (
            -(df["AskPrice1"] - aps) / df["AskPrice1"]
            - (df["BidPrice1"] - bps) / df["BidPrice1"]
        )

        n = 5
        bid_prices = [f"BidPrice{i}" for i in range(1, n + 1)]
        ask_prices = [f"AskPrice{i}" for i in range(1, n + 1)]
        prices = bid_prices + ask_prices
        df["depth_price_skew"] = df[prices].skew(axis=1)
        df["depth_price_kurt"] = df[prices].kurt(axis=1)

        window_size = 60
        df["rolling_return"] = (
            df["MidPrice"].diff(window_size) / df["MidPrice"]
        ).fillna(0)

        window_size = 60
        df["quasi"] = df["AskPrice1"].diff().abs().rolling(window_size).sum().fillna(0)
        window_size = 60
        df["avg_spread"] = (
            (df["AskPrice1"] - df["BidPrice1"]).rolling(window_size).mean().fillna(0)
        )
        volume_columns = [f"AskVolume{i}" for i in range(1, 11)] + [
            f"BidVolume{i}" for i in range(1, 11)
        ]
        df["avg_turnover"] = df[volume_columns].sum(axis=1)
        window_size = 60
        df["avg_trade_volume"] = (
            df["Volume"]
            .abs()
            .rolling(window_size)
            .sum()
            .shift(-window_size + 1)
            .fillna(0)
        )

        window_size = 100
        df["volume_kurt"] = df["Volume"].rolling(window_size).kurt().fillna(0)
        df["volume_skew"] = df["Volume"].rolling(window_size).skew().fillna(0)

        total_volume = avs + bvs
        weighted_price = (aps + bps) / total_volume
        df["weighted_price_to_mid"] = weighted_price - df["MidPrice"]

        df = df[feature_col]
        res = df.iloc[-1]
        # logger.debug(f"Prepard Model Data for {stock}:")
        # print(res)
        end_time = time.time()  # End timing
        duration = end_time - start_time
        # logger.debug(f"Get Model Data execution time: {duration} seconds")

        return res
