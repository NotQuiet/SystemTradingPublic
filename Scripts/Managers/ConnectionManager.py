from Scripts.Controllers.GetBinanceDataController import BinanceDataController
from Scripts.Controllers.GetClientDataController import  ClientDataController
from binance.client import Client

from Scripts.Controllers.BinanceSocketController import BinanceSocketController


def testSocket(client: Client):
    BinanceSocketController(client)


class ConnectionManager:
    client: Client
    binanceDataController: BinanceDataController
    clientDataController: ClientDataController


    def __init__(self, binance_client: Client):
        testSocket(binance_client)




