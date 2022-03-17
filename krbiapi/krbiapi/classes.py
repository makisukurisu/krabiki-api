import websockets, json, requests, asyncio, datetime
class SocketWorker():

    def __init__(self, con_url: str, token = None, curr_pairs = []) -> None:
        self.Url = con_url
        self.Token = token
        
        self.CurrencyPairs = curr_pairs
    
    def getCurrency(self, name):
        raise NotImplemented()

class KrakenWorker(SocketWorker):

    def __init__(self, con_url = "wss://ws.kraken.com", token=None, curr_pairs=[]) -> None:
        super().__init__(con_url, token, curr_pairs)
        if self.CurrencyPairs == []:
            self.CurrencyPairs = self.getPairs()
    
    def getPairs(self):

        resp = requests.get("https://api.kraken.com/0/public/AssetPairs")
        json_ = resp.json()
        if json_["error"] != []:
            raise Exception("Kraken REST API AssertPairs returned error", json_)
        
        PairArray = []
        for x in json_["result"].values():
            PairArray.append({
                "name": x["wsname"],
                "altname": x["altname"],
                "base": x["base"].replace("X", "", 1),
                "quote": x["quote"].replace("X", "", 1)
            })
        
        return PairArray

    def getName(self, name):
        if name.find("/") > 0:
            for x in self.CurrencyPairs:
                if x["name"] == name:
                    return x["name"]
        elif name.find("_") > 0:
            tempname = name.replace("_", "", 1)
            for x in self.CurrencyPairs:
                if x["altname"] == tempname:
                    return x["name"]
        else:
            for x in self.CurrencyPairs:
                if name in [x["name"], x["altname"]]:
                    return x["name"]
    
    def recv_processor(self, recv):
        try:
            processed = {"Name": recv[-1], "Price": (float(recv[1]["a"][0]) + float(recv[1]["b"][0]))/2, "PID": recv[0]}
            return processed
        except Exception as E:
            raise Exception(E, recv)
    
    async def _get_currency(self, names):
        async with websockets.connect(self.Url) as ws:
            await ws.send(json.dumps({"event": "subscribe", "pair": names, "subscription": {"name": "ticker"}}))
            con_id = await ws.recv()
            if len(names) == 1:
                sub_info = json.loads(await ws.recv())
                if sub_info["event"] == "error":
                    raise Exception("Error from Karken exchange", sub_info)

                showOK = True
            else:
                showOK = False
            responses = []
            while True:
                recv = json.loads(await ws.recv())
                try:
                    if recv["event"] == 'subscriptionStatus':
                        continue
                except TypeError:
                    None
                if recv == {"event": "heartbeat"}:
                    break
                if recv != None:
                    responses.append(self.recv_processor(recv))
            if len(responses) == 1:
                return responses[0]
            else:
                return responses

    def getCurrency(self, name):
        exchange_name = self.getName(name)
        if exchange_name == None:
            return Error("Pair not found {}".format(name), name=name, allPairs=self.CurrencyPairs)
        result = asyncio.run(self._get_currency([exchange_name]))
        return Response(Pair=result)
    
    def getAllCurrencies(self):
        results = asyncio.run(self._get_currency([pair["name"] for pair in self.CurrencyPairs]))
        return Response(AllPairs=results)

class BinanceWorker(SocketWorker):

    def __init__(self, con_url = "wss://stream.binance.com/ws", token=None, curr_pairs=[]) -> None:
        super().__init__(con_url, token, curr_pairs)
        if self.CurrencyPairs == []:
            self.CurrencyPairs = self.getPairs()
    
    def getPairs(self):
        
        resp = requests.get("https://api.binance.com/api/v1/exchangeInfo")
        json_ = resp.json()
        
        PairArray = []
        for x in json_["symbols"]:
            if x["status"] != "TRADING": continue
            PairArray.append({
                "name": x["symbol"],
                "base": x["baseAsset"],
                "quote": x["quoteAsset"],
                "altname": "{}_{}".format(x["baseAsset"], x["quoteAsset"])
            })
        
        return PairArray
    
    def getName(self, name):
        name = name.replace("/", "", 1)
        if name.find("_") > 0:
            name = name.replace("_", "", 1)
            for x in self.CurrencyPairs:
                if x["name"] == name:
                    return x["name"]
        else:
            for x in self.CurrencyPairs:
                if x["name"] == name:
                    return x["name"]
    
    def recv_processor(self, recv):
        try:
            processed = {"Name": recv["s"], "Price": (float(recv["b"]) + float(recv["a"]))/2}
            return processed
        except Exception as E:
            raise Exception(E, recv)

    async def _get_currency(self, name):
        async with websockets.connect(self.Url) as ws:
            await ws.send(json.dumps({"method": "SUBSCRIBE", "params": [name.lower()+"@ticker"], "id": int(datetime.datetime.now().timestamp())}))
            confirmation = await ws.recv()
            ticker = json.loads(await ws.recv())
            return self.recv_processor(ticker)

    def getCurrency(self, name):
        exchange_name = self.getName(name)
        if exchange_name == None:
            return Error("Pair not found {}".format(name), passed_name=name, allPairs=self.CurrencyPairs)
        result = asyncio.run(self._get_currency(exchange_name))
        return Response(Pair=result)
    
    async def _get_all(self):
        async with websockets.connect(self.Url) as ws:
            await ws.send(
                json.dumps({
                    "method": "SUBSCRIBE", "params": ["!ticker@arr"], "id": int(datetime.datetime.now().timestamp())
                })
            )
            confirmation = await ws.recv()
            tickers = json.loads(await ws.recv())
            processed_list = []
            for tick in tickers:
                processed_list.append(self.recv_processor(tick))
            return processed_list

    def getAllCurrencies(self):
        results = asyncio.run(self._get_all())
        return Response(AllPairs=results)

class Throwable():

    def __init__(self) -> None:
        self.msg = None

    def throw(self):
        return self.msg

class Error(Throwable):

    def __init__(self, message, **kwargs) -> None:
        super().__init__()
        self.msg = {"State": "Error", "error": message, "Response": kwargs}

class Response(Throwable):

    def __init__(self, state="Ok", **kwargs) -> None:
        super().__init__()
        if state != None:
            self.msg = {"State": state, "Response": kwargs}
        else:
            self.msg = {"Response": kwargs}