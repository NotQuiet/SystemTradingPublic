class IncomeTreeDataDto:
    currentPrice: float = 0.0
    lastPrice: float = 0.0
    volume: float = 0.0
    periodInSeconds: float = 0.0
    overbought: bool = False
    oversold: bool = False

    def __init__(self, currentPrice: float, lastPrice: float, volume: float,
                 periodInSeconds: float, overbought: bool, oversold: bool):
        self.currentPrice = currentPrice
        self.lastPrice = lastPrice
        self.volume = volume
        self.periodInSeconds = periodInSeconds
        self.overbought = overbought
        self.oversold = oversold



