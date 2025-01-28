from Scripts.DecisionTree.TreeNode import Node
from Scripts.DecisionTree.Signals.SignalManager import SignalManager
import asyncio
import time

class OpenInterestProcessorNode(Node):
    def __init__(self, name, signal_manager: SignalManager):
        super().__init__(name)
        self.signal_manager = signal_manager
        self.threshold_percentage = 3.0
        self.last_alert_time = {}

    async def analyze(self, data, interval):
        if interval in self.ignore_time_frames:
            return
        self.interval = interval
        tasks = [
            self.detect_open_interest_change(symbol, values['open_interest'])
            for symbol, values in data.items()
        ]
        await asyncio.gather(*tasks)
        print(f"---   {self.name} node analyze process completed for all symbols on interval {interval}.")

    async def detect_open_interest_change(self, symbol, open_interest_list):
        if not open_interest_list or len(open_interest_list) < 4:
            print(f"Недостаточно данных об открытом интересе для {symbol} на интервале {self.interval}.")
            return

        recent_oi = open_interest_list[-4:]
        percentage_change = ((recent_oi[-1] - recent_oi[0]) / recent_oi[0]) * 100

        if abs(percentage_change) >= self.threshold_percentage:
            if self.should_send_alert(symbol):
                if percentage_change > 0:
                    await self.on_open_interest_increased(symbol, percentage_change)
                else:
                    await self.on_open_interest_decreased(symbol, percentage_change)
                self.update_last_alert_time(symbol)

    def should_send_alert(self, symbol):
        current_time = time.time()
        cooldown = self.get_cooldown_seconds()
        if cooldown is None:
            print(f"Интервал {self.interval} не распознан.")
            return False

        last_time = self.last_alert_time.get((symbol, self.interval), 0)
        if current_time - last_time >= cooldown:
            return True
        else:
            return False

    def update_last_alert_time(self, symbol):
        self.last_alert_time[(symbol, self.interval)] = time.time()

    def get_cooldown_seconds(self):
        interval_seconds = self.interval_to_seconds(self.interval)
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

    async def on_open_interest_increased(self, symbol, percentage_change):
        signal_data = {
            'direction': 'increase',
            'percentage_change': percentage_change
        }
        await self.signal_manager.process_signal(symbol, self.interval, 'OpenInterest', signal_data)

    async def on_open_interest_decreased(self, symbol, percentage_change):
        signal_data = {
            'direction': 'decrease',
            'percentage_change': percentage_change
        }
        await self.signal_manager.process_signal(symbol, self.interval, 'OpenInterest', signal_data)
