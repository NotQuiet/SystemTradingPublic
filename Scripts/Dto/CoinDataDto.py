class CoinDataDto:
    symbol: str = ''
    price: float = 0.0

    def __init__(self, symbol: str, price: float):
        self.symbol = symbol
        self.price = price
