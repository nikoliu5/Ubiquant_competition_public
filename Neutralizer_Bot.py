from interface_class import InterfaceClass
from data_manager import DataManager
from broker import Broker
from strategy import Strategy
from trade_mgmt import Side
import requests
import socket
import json
import time
import logging
import random
import uuid
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Type, Union
import aiohttp
import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
import sys
from collections import deque
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
import itertools
import os

# import numba as nb


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def ConvertToSimTime_us(start_time, time_ratio, day, running_time):
    return (time.time() - start_time - (day - 1) * running_time) * time_ratio


class NeutralizerBotsClass:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.api = InterfaceClass("https://trading.competition.ubiquant.com")
        # self.init_cash = init_cash
        # self.curr_cash = init_cash
        # self.tot_bp = init_cash
        # self.init_position = 0
        # self.tot_position = 0
        # self.actual_pnl = 0
        # self.actual_sharpe = 0
        # self.score = 0

    # TODO: Update Async to all functions
    def login(self):
        response = self.api.sendLogin(self.username, self.password)
        if response["status"] == "Success":
            self.token_ub = response["token_ub"]
            logger.info("Login Success: {}".format(self.token_ub))
        else:
            logger.info("Login Error: ", response["status"])

    def GetInstruments(self):
        response = self.api.sendGetInstrumentInfo(self.token_ub)
        if response["status"] == "Success":
            self.instruments = []
            for instrument in response["instruments"]:
                self.instruments.append(instrument["instrument_name"])
            logger.info("Get Instruments: {}".format(self.instruments))

    def init(self):
        response = self.api.sendGetGameInfo(self.token_ub)
        if response["status"] == "Success":
            self.start_time = response["next_game_start_time"]
            self.running_days = response["next_game_running_days"]
            self.running_time = response["next_game_running_time"]
            self.time_ratio = response["next_game_time_ratio"]
            # logger.debug(f"Init Success: {response['status']}")
            logger.debug(f"Start_time: {self.start_time}")
            logger.debug(f"Running_days: {self.running_days}")
            logger.debug(f"Running_time: {self.running_time}")
            logger.debug(f"Time_ratio: {self.time_ratio}")
            self.time_info = (
                self.start_time,
                self.running_days,
                self.running_time,
                self.time_ratio,
            )
        else:
            logger.debug(f"Init Error: {response['status']}")
        self.GetInstruments()
        self.day = 0

    def cancel_active_orders(self):
        response = self.api.sendGetActiveOrder(self.token_ub)
        if response["status"] == "Success":
            logger.debug(f"Cancel All Active Orders ------------------")
            for instrument_orders in response["instruments"]:
                if len(instrument_orders["active_orders"]) != 0:
                    for order in instrument_orders["active_orders"]:
                        t = ConvertToSimTime_us(*self.time_info)
                        self.api.sendCancel(
                            self.token_ub,
                            instrument_orders["instrument_name"],
                            t,
                            order["order_index"],
                        )
                        logger.debug(
                            f"Cancel Order: Instrument:{instrument_orders['instrument_name']} Order_index: {order['order_index']}"
                        )
        else:
            logger.debug(f"Cancel Order Error: {response['status']}")

    def bod(self):
        self.cancel_active_orders()
        self.data_manager = DataManager(self.instruments, self.api, self.token_ub)
        self.broker = Broker(
            self.instruments, self.api, self.token_ub, self.data_manager, self.time_info
        )
        self.strategy = Strategy(self.instruments, self.data_manager, self.broker)
        self.broker.set_stock_trade_list(self.strategy.stock_trade_list)
        self.broker.init_broker()

    async def work(self):
        # Time update_lob
        start_time = time.time()
        await self.data_manager.update_lob()
        end_time = time.time()
        # print(f"update_lob took {end_time - start_time} seconds")

    def test_order(self):
        stockID = 1
        t = ConvertToSimTime_us(
            self.start_time, self.time_ratio, self.day, self.running_time
        )
        self.broker.submit_market_order(self.instruments[stockID], Side.BUY, 100, t)

    async def update_info(self):
        # Time get_trade_info
        start_time = time.time()
        await self.broker.get_trade_info()
        end_time = time.time()
        print(f"get_trade_info took {end_time - start_time} seconds")
        self.broker.calibrate_broker()

        # self.broker.get_pos_manager_info()

    def neutralize_strategy(self):
        self.cancel_active_orders()
        self.broker.neutralize_all("best")

    def run_strategy(self):
        self.strategy.trade_decision_all()

    def risk_management(self):
        self.broker.risk_management_all()

    def near_eod(self):
        self.cancel_active_orders()
        self.broker.neutralize_all("second_best")

    def eod(self):
        logger.debug(f"End of Day Result--------------------------")
        self.broker.get_stats()
        self.broker.clean_init_positions()

        pass

    def final(self):
        logger.debug(f"Final Result---------------------------------")
        self.broker.get_stats()


async def main():
    init_cash = 1000000
    bot = NeutralizerBotsClass("UBIQ_TEAMXXX", "XXXXXXXXX")
    bot.login()
    bot.init()
    SimTimeLen = 14400
    endWaitTime = 300

    while True:
        if (
            ConvertToSimTime_us(
                bot.start_time, bot.time_ratio, bot.day, bot.running_time
            )
            < SimTimeLen
        ):
            break
        else:
            bot.day += 1

    while bot.day <= bot.running_days:
        while True:
            if (
                ConvertToSimTime_us(
                    bot.start_time, bot.time_ratio, bot.day, bot.running_time
                )
                > -900
            ):
                break
        bot.bod()
        eod_process = False
        now = round(
            ConvertToSimTime_us(
                bot.start_time, bot.time_ratio, bot.day, bot.running_time
            )
        )
        for s in range(now, SimTimeLen + endWaitTime):
            while True:
                if (
                    ConvertToSimTime_us(
                        bot.start_time, bot.time_ratio, bot.day, bot.running_time
                    )
                    >= s
                ):
                    break
            t = ConvertToSimTime_us(
                bot.start_time, bot.time_ratio, bot.day, bot.running_time
            )
            logger.info("Work Time: {}".format(t))
            if t < 0:
                continue
            if t < SimTimeLen - 60:
                await bot.work()
                # logger.info("s(game) time: {}".format(s))
                if s % 5 == 0:
                    await bot.update_info()
                if s % 30 == 0:
                    bot.neutralize_strategy()
                # if s % 20 == 0:
                #     bot.run_strategy()
                # if s % 200 == 0:
                #     bot.test_order()
            else:
                if not eod_process:
                    bot.near_eod()
                    eod_process = True
        bot.eod()
        bot.day += 1
    bot.final()


if __name__ == "__main__":
    asyncio.run(main())
