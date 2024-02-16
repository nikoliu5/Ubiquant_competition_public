import requests
import socket
import json
import time
import logging
import random
import aiohttp
import asyncio


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def ConvertToSimTime_us(start_time, time_ratio, day, running_time):
    return (time.time() - start_time - (day - 1) * running_time) * time_ratio

class BotsClass:
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def login(self):
        pass
    def init(self):
        pass
    def bod(self):
        pass
    def work(self):
        pass
    def eod(self):
        pass
    def final(self):
        pass

class BotsDemoClass(BotsClass):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.api = InterfaceClass("https://trading.competition.ubiquant.com")
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
        self.GetInstruments()
        self.day = 0
    def bod(self):
        pass        
    async def work(self): 
        # stockID = 1
        start_time = time.time()
        await self.process_all_stocks()
        end_time = time.time()
        logger.info(f"Time taken for LOB update: {end_time - start_time} seconds")
    async def process_all_stocks(self):
        tasks = [self.handle_stock(stockID) for stockID in range(29)]
        await asyncio.gather(*tasks)

    async def handle_stock(self, stockID):
        LOB = await self.api.sendGetLimitOrderBookAsync(self.token_ub, self.instruments[stockID])
        if LOB["status"] == "Success":
            print('Updated LOB stock {}'.format(stockID))
            # askprice_1 = float(LOB["lob"]["askprice"][0])
            # t = ConvertToSimTime_us(self.start_time, self.time_ratio, self.day, self.running_time)
            # response = self.api.sendOrder(self.token_ub, self.instruments[stockID], t, "buy", askprice_1, 100)
        
    def eod(self):
        pass
    def final(self):
        pass

class InterfaceClass:
    def __init__(self, domain_name):
        self.domain_name = domain_name
        self.session = requests.Session()
        self.async_session = aiohttp.ClientSession()
    def sendLogin(self, username, password):
        url = self.domain_name + "/api/Login"
        data = {
            "user": username,
            "password": password
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response
    
    def sendGetGameInfo(self, token_ub):
        url = self.domain_name + "/api/TradeAPI/GetGAmeInfo"

    def sendOrder(self, token_ub, instrument, localtime, direction, price, volume):
        logger.debug("Order: Instrument: {}, Direction:{}, Price: {}, Volume:{}".format(instrument, direction, price, volume))
        url = self.domain_name + "/api/TradeAPI/Order"
        data = {
            "token_ub": token_ub,
            "user_info": "NULL",
            "instrument": instrument,
            "localtime": localtime,
            "direction": direction,
            "price": price,
            "volume": volume,
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendCancel(self, token_ub, instrument, localtime, index):
        logger.debug("Cancel: Instrument: {}, index:{}".format(instrument, index))
        url = self.domain_name + "/api/TradeAPI/Cancel"
        data = {
            "token_ub": token_ub,
            "user_info": "NULL",
            "instrument": instrument,
            "localtime": 0,
            "index": index
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendGetLimitOrderBook(self, token_ub, instrument):
        logger.debug("GetLimitOrderBOok: Instrument: {}".format(instrument))
        url = self.domain_name + "/api/TradeAPI/GetLimitOrderBook"
        data = {
            "token_ub": token_ub,
            "instrument": instrument
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    async def sendGetLimitOrderBookAsync(self, token_ub, instrument):
        # logger.debug("GetLimitOrderBook: Instrument: {}".format(instrument))
        url = self.domain_name + "/api/TradeAPI/GetLimitOrderBook"
        data = {
            "token_ub": token_ub,
            "instrument": instrument
        }
        async with self.async_session.post(url, data=json.dumps(data)) as response:
            return await response.json()

    def sendGetUserInfo(self, token_ub):
        logger.debug("GetUserInfo: ")
        url = self.domain_name + "/api/TradeAPI/GetUserInfo"
        data = {
            "token_ub": token_ub,
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendGetGameInfo(self, token_ub):
        logger.debug("GetGameInfo: ")
        url = self.domain_name + "/api/TradeAPI/GetGameInfo"
        data = {
            "token_ub": token_ub,
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendGetInstrumentInfo(self, token_ub):
        logger.debug("GetInstrumentInfo: ")
        url = self.domain_name + "/api/TradeAPI/GetInstrumentInfo"
        data = {
            "token_ub": token_ub,
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendGetTrade(self, token_ub, instrument):
        logger.debug("GetTrade: Instrment: {}".format(instrument))
        url = self.domain_name + "/api/TradeAPI/GetTrade"
        data = {
            "token_ub": token_ub,
            "instrument_name": instrument
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendGetActiveOrder(self, token_ub):
        logger.debug("GetActiveOrder: ")
        url = self.domain_name + "/api/TradeAPI/GetActiveOrder"
        data = {
            "token_ub": token_ub,
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response



async def main():
    bot = BotsDemoClass("UBIQ_TEAM077", "k147U6woN")
    bot.login()
    bot.init()
    SimTimeLen = 14400
    endWaitTime = 300
    while True:
        if ConvertToSimTime_us(bot.start_time, bot.time_ratio, bot.day, bot.running_time) < SimTimeLen:
            break
        else:
            bot.day += 1

    while bot.day <= bot.running_days:
        while True:
            if ConvertToSimTime_us(bot.start_time, bot.time_ratio, bot.day, bot.running_time) > -900:
                break
        bot.bod()
        now = round(ConvertToSimTime_us(bot.start_time, bot.time_ratio, bot.day, bot.running_time))
        for s in range(now, SimTimeLen + endWaitTime):
            while True:
                if ConvertToSimTime_us(bot.start_time, bot.time_ratio, bot.day, bot.running_time) >= s:
                    break
            t = ConvertToSimTime_us(bot.start_time, bot.time_ratio, bot.day, bot.running_time)
            logger.info("Work Time: {}".format(t))
            if t < SimTimeLen - 30:
                await bot.work()
        bot.eod()
        bot.day += 1
    bot.final()

if __name__ == "__main__":
    asyncio.run(main())