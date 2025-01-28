from binance.client import Client


from Scripts.Dto.CoinDataDto import CoinDataDto

class BinanceDataController:

        client: Client

        def __init__(self, client: Client):
                self.client = client

        def GetBTCUSDT(self)->CoinDataDto:
                btc_price = self.client.get_symbol_ticker(symbol="BTCUSDT")
                data = CoinDataDto(btc_price["symbol"], btc_price["price"])
                return data
