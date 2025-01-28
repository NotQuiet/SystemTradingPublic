import uuid  # Добавляем импорт модуля uuid
from datetime import datetime

class Transaction:
    def __init__(self, symbol, entry_price, direction, stop_loss, take_profit, interval=None):
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.entry_price = entry_price
        self.exit_price = None
        self.direction = direction
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.profit_loss_percentage = None
        self.active = True
        self.interval = interval
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.freeze_until = None
        self.highest_price = entry_price if direction == "long" else None
        self.lowest_price = entry_price if direction == "short" else None
