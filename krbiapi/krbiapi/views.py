from django.http import JsonResponse

from . import classes

KW = classes.KrakenWorker()
BW = classes.BinanceWorker()

exchangeNames = ["kraken", "binance"]

def getPE(request, **kwargs):
    pair = kwargs["pair"]
    exchange = kwargs["exchange"]
    
    Result = None

    if exchange not in exchangeNames:
        return JsonResponse(
            classes.Error("Invalid exchange name, acceptable: {}".format(exchangeNames), accepting=exchangeNames, other=[pair, exchange]).throw()
            )
    if exchange.lower() == "kraken":
        Result = KW.getCurrency(pair)
    if exchange.lower() == "binance":
        Result = BW.getCurrency(pair)
    try:
        return JsonResponse(Result)
    except:
        return JsonResponse(Result.throw())

def getP(request, **kwargs):
    pair = kwargs["pair"]
    
    Results = {}
    
    Results["kraken"] = KW.getCurrency(pair)
    Results["binance"] = BW.getCurrency(pair)

    if isinstance(Results["kraken"], classes.Error) and isinstance(Results["binance"], classes.Error):
        return JsonResponse(
            classes.Error("Error with both exchanges", krakenError=Results["kraken"], binanceError=Results["binance"]).throw()
            )
    else:
        ResultsValues = {}
        for exc in Results.items():
            ResultsValues[exc[0]] = exc[1].throw()
        return JsonResponse(
            classes.Response(Results=ResultsValues).throw()
        )

def getE(request, **kwargs):
    exchange = kwargs["exchange"]
    
    if exchange not in exchangeNames:
        return JsonResponse(
            classes.Error("Invalid exchange name: {}, acceptable: {}".format(exchange, exchangeNames), accepting=exchangeNames).throw()
            )

    if exchange.lower() == "kraken":
        Result = KW.getAllCurrencies()
    if exchange.lower() == "binance":
        Result = BW.getAllCurrencies()
    
    return JsonResponse(Result.throw())

def getNone(request, **kwargs):

    Results = {}
    
    Results["kraken"] = KW.getAllCurrencies().throw()
    Results["binance"] = BW.getAllCurrencies().throw()

    Merge = []
    for ccy in Results["kraken"]["Response"]["AllPairs"]:
        ccy["Source"] = "kraken"
        Merge.append(ccy)
    for ccy in Results["binance"]["Response"]["AllPairs"]:
        ccy["Source"] = "binance"
        Merge.append(ccy)

    ### Or this
    # ResultsValues = {}
    # for exc in Results.items():
    #     ResultsValues[exc[0]] = exc[1].throw()
    # return JsonResponse(
    #     classes.Response(Results=ResultsValues).throw()
    # )

    return JsonResponse(
        classes.Response(AllPairs=Merge).throw()
    )