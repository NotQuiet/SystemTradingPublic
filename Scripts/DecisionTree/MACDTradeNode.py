import pandas as pd
import asyncio

from Scripts.DecisionTree.TreeNode import Node
from Scripts.DecisionTree.Transactions.TransactionsManager import TransactionManager

class MACDTradeNode(Node):

    def __init__(self, name, transaction_manager: TransactionManager):
        super().__init__(name)
        self.transaction_manager = transaction_manager
        self.macd_extremes = {}

    async def analyze(self, prices_dict: dict, interval: str):
        if interval in self.ignore_time_frames:
            return
        self.interval = interval
        tasks = [
            self.calculate_macd(tokenPair, data['prices'], interval)
            for tokenPair, data in prices_dict.items()
        ]
        await asyncio.gather(*tasks)
        print(f"--- {self.name} node analyze process completed for all token pairs on interval {interval}.")

    async def calculate_macd(self, tokenPair, prices, interval):
        df = pd.DataFrame(prices, columns=['close'])

        if len(df) < 28:
            print(f"Недостаточно данных для анализа {tokenPair} на интервале {interval}.")
            return

        fast_length = 12
        slow_length = 26
        signal_length = 9

        fast_ema = df['close'].ewm(span=fast_length, adjust=False).mean()
        slow_ema = df['close'].ewm(span=slow_length, adjust=False).mean()

        macd_line = fast_ema - slow_ema

        macd_n2 = macd_line.iloc[-3]
        macd_n1 = macd_line.iloc[-2]
        macd_n = macd_line.iloc[-1]

        if tokenPair not in self.macd_extremes:
            self.macd_extremes[tokenPair] = {
                'max': macd_n2,
                'min': macd_n2,
                'last_direction': None,
                'last_macd': macd_n2
            }
            print(f"Инициализация MACD экстремумов для {tokenPair}.")
            return

        extremes = self.macd_extremes[tokenPair]
        last_max = extremes['max']
        last_min = extremes['min']
        last_direction = extremes['last_direction']
        last_macd = extremes['last_macd']

        if macd_n1 > last_max:
            extremes['max'] = macd_n1
        elif macd_n1 < last_min:
            extremes['min'] = macd_n1

        reversal = False
        new_direction = last_direction

        if last_direction == 'down':
            if macd_n1 > last_min:
                if macd_n > macd_n1:
                    reversal = True
                    new_direction = 'up'
        elif last_direction == 'up':
            if macd_n1 < last_max:
                if macd_n < macd_n1:
                    reversal = True
                    new_direction = 'down'
        else:
            if macd_n1 > last_macd:
                new_direction = 'up'
            elif macd_n1 < last_macd:
                new_direction = 'down'
            extremes['max'] = macd_n1
            extremes['min'] = macd_n1

        if reversal:
            print(f"MACD для {tokenPair} подтвердил смену направления с {last_direction} на {new_direction}.")
            await self.on_signal_change(tokenPair, new_direction, interval)
            extremes['max'] = macd_n1
            extremes['min'] = macd_n1

        extremes['last_direction'] = new_direction
        extremes['last_macd'] = macd_n1

        self.macd_extremes[tokenPair] = extremes

    async def on_signal_change(self, tokenPair, direction, interval):
        side = 'long' if direction == 'up' else 'short'
        existing_transaction = self.transaction_manager.get_active_transaction_by_symbol_and_interval(tokenPair,
                                                                                                      interval)

        if existing_transaction:
            print(f"По {tokenPair} на интервале {interval} уже есть открытая позиция. Новая позиция не будет открыта.")
        else:
            await self.transaction_manager.open_position(tokenPair, interval, side)
            print(f"Открыта {side.upper()} позиция для {tokenPair} на интервале {interval}")

