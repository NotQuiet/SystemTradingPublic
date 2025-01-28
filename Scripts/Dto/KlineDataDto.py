class KlineData:
    def __init__(self, event_type, event_time, symbol, interval, start_time, close_time, first_trade_id, last_trade_id, open_price, close_price, high_price, low_price, base_asset_volume, number_of_trades, is_closed, quote_asset_volume, taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore):
        self.event_type = event_type
        self.event_time = event_time
        self.symbol = symbol
        self.interval = interval
        self.start_time = start_time
        self.close_time = close_time
        self.first_trade_id = first_trade_id
        self.last_trade_id = last_trade_id
        self.open_price = open_price
        self.close_price = close_price
        self.high_price = high_price
        self.low_price = low_price
        self.base_asset_volume = base_asset_volume
        self.number_of_trades = number_of_trades
        self.is_closed = is_closed
        self.quote_asset_volume = quote_asset_volume
        self.taker_buy_base_asset_volume = taker_buy_base_asset_volume
        self.taker_buy_quote_asset_volume = taker_buy_quote_asset_volume
        self.ignore = ignore
