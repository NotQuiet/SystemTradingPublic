import pandas as pd
import asyncio

from Scripts.DecisionTree.TreeNode import Node
from Scripts.DecisionTree.Signals.SignalManager import SignalManager

class MACDProcessorNode(Node):

    def __init__(self, name, signal_manager: SignalManager):
        super().__init__(name)
        self.signal_manager = signal_manager
        self.threshold = 1e-6

    async def analyze(self, prices_dict: dict, interval: str):
        if interval in self.ignore_time_frames:
            return
        self.interval = interval
        tasks = [
            self.calculate_macd(tokenPair, data['prices'], interval)
            for tokenPair, data in prices_dict.items()
        ]
        await asyncio.gather(*tasks)
        print(f"---   {self.name} node analyze process completed for all token pairs on interval {interval}.")

    async def calculate_macd(self, tokenPair, prices, interval):
        df = pd.DataFrame(prices, columns=['close'])

        if len(df) < 3:
            print(f"Недостаточно данных для анализа {tokenPair} на интервале {interval}.")
            return

        fast_length = 12
        slow_length = 26
        signal_length = 9

        fast_ma = df['close'].ewm(span=fast_length, adjust=False).mean()
        slow_ma = df['close'].ewm(span=slow_length, adjust=False).mean()

        macd_line = fast_ma - slow_ma
        signal_line = macd_line.ewm(span=signal_length, adjust=False).mean()

        macd_diff = macd_line - signal_line

        macd_diff_prev = macd_diff.iloc[-3]
        macd_diff_cross = macd_diff.iloc[-2]
        macd_diff_current = macd_diff.iloc[-1]

        if (macd_diff_prev < -self.threshold and macd_diff_cross > self.threshold):
            if macd_diff_current > self.threshold:
                await self.on_macd_change(tokenPair, 'change_up')
        elif (macd_diff_prev > self.threshold and macd_diff_cross < -self.threshold):
            if macd_diff_current < -self.threshold:
                await self.on_macd_change(tokenPair, 'change_down')


    async def on_macd_change(self, tokenPair, direction):
        signal_data = {
            'direction': direction
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'MACD', signal_data)
        print(f"MACD изменился для {tokenPair} на интервале {self.interval}")
