import requests
import aiohttp
import json


class InterfaceClass:
    def __init__(self, domain_name):
        self.domain_name = domain_name
        self.session = requests.Session()
        self.async_session = aiohttp.ClientSession()

    def sendLogin(self, username, password):
        url = self.domain_name + "/api/Login"
        data = {"user": username, "password": password}
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendGetGameInfo(self, token_ub):
        url = self.domain_name + "/api/TradeAPI/GetGAmeInfo"

    def sendOrder(self, token_ub, instrument, localtime, direction, price, volume):
        logger.debug(
            "Order: Instrument: {}, Direction:{}, Price: {}, Volume:{}".format(
                instrument, direction, price, volume
            )
        )
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
            "index": index,
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    def sendGetLimitOrderBook(self, token_ub, instrument):
        # logger.debug("GetLimitOrderBOok: Instrument: {}".format(instrument))
        url = self.domain_name + "/api/TradeAPI/GetLimitOrderBook"
        data = {"token_ub": token_ub, "instrument": instrument}
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    async def sendGetLimitOrderBookAsync(self, token_ub, instrument):
        # logger.debug("GetLimitOrderBOok: Instrument: {}".format(instrument))
        url = f"{self.domain_name}/api/TradeAPI/GetLimitOrderBook"
        data = {"token_ub": token_ub, "instrument": instrument}
        async with self.async_session.post(url, data=json.dumps(data)) as response:
            return await response.json()

    def sendGetUserInfo(self, token_ub):
        # logger.debug("GetUserInfo: ")
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
        # logger.debug("GetTrade: Instrment: {}".format(instrument))
        url = self.domain_name + "/api/TradeAPI/GetTrade"
        data = {"token_ub": token_ub, "instrument_name": instrument}
        response = self.session.post(url, data=json.dumps(data)).json()
        return response

    async def sendGetTradeAsync(self, token_ub, instrument):
        # logger.debug("GetTrade: Instrment: {}".format(instrument))
        url = self.domain_name + "/api/TradeAPI/GetTrade"
        data = {"token_ub": token_ub, "instrument_name": instrument}
        async with self.async_session.post(url, data=json.dumps(data)) as response:
            return await response.json()

    def sendGetActiveOrder(self, token_ub):
        logger.debug("GetActiveOrder: ")
        url = self.domain_name + "/api/TradeAPI/GetActiveOrder"
        data = {
            "token_ub": token_ub,
        }
        response = self.session.post(url, data=json.dumps(data)).json()
        return response
