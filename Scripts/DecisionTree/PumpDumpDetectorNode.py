import pandas as pd
import asyncio
import time

from Scripts.DecisionTree.TreeNode import Node
from Scripts.DecisionTree.Signals.SignalManager import SignalManager

class PumpDumpDetectorNode(Node):

    def __init__(self, name, signal_manager: SignalManager):
        super().__init__(name)
        self.signal_manager = signal_manager
        self.threshold_percentage = 1.0
        self.last_alert_time = {}

    async def analyze(self, prices_dict: dict, interval: str):
        if interval in self.ignore_time_frames:
            return
        self.interval = interval
        tasks = [
            self.detect_pump_dump(tokenPair, data['prices'], interval)
            for tokenPair, data in prices_dict.items()
        ]
        await asyncio.gather(*tasks)
        print(f"---   {self.name} node analyze process completed for all token pairs on interval {interval}.")

    async def detect_pump_dump(self, tokenPair, prices, interval):
        df = pd.DataFrame(prices, columns=['close'])

        if len(df) < 2:
            print(f"Недостаточно данных для анализа {tokenPair} на интервале {interval}.")
            return

        last_two_closes = df['close'].iloc[-2:]
        average_close = last_two_closes.iloc[:-1].mean()
        last_close = last_two_closes.iloc[-1]

        price_change = ((last_close - average_close) / average_close) * 100

        if price_change >= self.threshold_percentage:
            await self.on_pump_detected(tokenPair, price_change)
        elif price_change <= -self.threshold_percentage:
            await self.on_dump_detected(tokenPair, price_change)

    def should_send_alert(self, tokenPair, interval):
        current_time = time.time()
        cooldown = self.get_cooldown_seconds(interval)
        if cooldown is None:
            return False

        last_time = self.last_alert_time.get((tokenPair, interval), 0)
        if current_time - last_time >= cooldown:
            return True
        else:
            return False

    def update_last_alert_time(self, tokenPair, interval):
        self.last_alert_time[(tokenPair, interval)] = time.time()

    def get_cooldown_seconds(self, interval):
        interval_seconds = self.interval_to_seconds(interval)
        if interval_seconds is not None:
            cooldown = interval_seconds / 2
            return cooldown
        else:
            return None

    def interval_to_seconds(self, interval):
        mapping = {
            '1s': 1,
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '2h': 7200,
            '4h': 14400,
            '6h': 21600,
            '8h': 28800,
            '12h': 43200,
            '1d': 86400,
            '3d': 259200,
            '1w': 604800,
            '1M': 2592000,
        }
        return mapping.get(interval, None)

    async def on_pump_detected(self, tokenPair, price_change):
        signal_data = {
            'direction': 'pump',
            'price_change': price_change
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'PumpDump', signal_data)
        print(f"Обнаружен памп для {tokenPair} на интервале {self.interval}")

    async def on_dump_detected(self, tokenPair, price_change):
        signal_data = {
            'direction': 'dump',
            'price_change': price_change
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'PumpDump', signal_data)
        print(f"Обнаружен дамп для {tokenPair} на интервале {self.interval}")
