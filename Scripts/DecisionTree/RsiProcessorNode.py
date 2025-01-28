import numpy as np
import asyncio

from Scripts.DecisionTree.TreeNode import Node
from Scripts.DecisionTree.Signals.SignalManager import SignalManager


class RsiProcessorNode(Node):

    def __init__(self, name, signal_manager: SignalManager, rsi_length=14, upper_bound=75, lower_bound=25):
        super().__init__(name)
        self.interval = "0m"
        self.children = []
        self.rsi_length = rsi_length
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.previous_rsi_values = {}
        self.signal_manager = signal_manager

    async def analyze(self, prices_dict: dict, interval: str):
        if interval in self.ignore_time_frames:
            return

        self.interval = interval
        for tokenPair, data in prices_dict.items():
            prices = data['prices']
            await self.detect_rsi_cross(tokenPair, prices, interval)
        print(f"---   {self.name} node analyze process completed for all token pairs.")

    async def detect_rsi_cross(self, tokenPair, prices, interval: str):
        rsi = self.calculate_rsi(prices)

        if len(rsi) < 2:
            return

        last_rsi = rsi[-1]
        prev_rsi = rsi[-2]

        previous_rsi = self.previous_rsi_values.get(tokenPair, {}).get(interval, {'last': None, 'prev': None})

        if prev_rsi <= self.upper_bound < last_rsi:
            await self.on_upper_bound(tokenPair, last_rsi, prices[-1])

        elif prev_rsi >= self.lower_bound > last_rsi:
            await self.on_lower_bound(tokenPair, last_rsi, prices[-1])

        if tokenPair not in self.previous_rsi_values:
            self.previous_rsi_values[tokenPair] = {}
        self.previous_rsi_values[tokenPair][interval] = {'last': last_rsi, 'prev': prev_rsi}

    def calculate_rsi(self, prices):
        deltas = np.diff(prices)
        seed = deltas[:self.rsi_length + 1]
        up = seed[seed >= 0].sum() / self.rsi_length
        down = -seed[seed < 0].sum() / self.rsi_length

        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:self.rsi_length] = 100. - 100. / (1. + rs) if down != 0 else 100.

        for i in range(self.rsi_length, len(prices)):
            delta = deltas[i - 1]
            upval = delta if delta > 0 else 0
            downval = -delta if delta < 0 else 0

            up = (up * (self.rsi_length - 1) + upval) / self.rsi_length
            down = (down * (self.rsi_length - 1) + downval) / self.rsi_length

            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs) if down != 0 else 100.

        return rsi

    async def on_upper_bound(self, tokenPair, rsi_value, price):
        signal_data = {
            'direction': 'cross_up',
            'rsi_value': rsi_value,
            'price': price
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'RSI', signal_data)

    async def on_lower_bound(self, tokenPair, rsi_value, price):
        signal_data = {
            'direction': 'cross_down',
            'rsi_value': rsi_value,
            'price': price
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'RSI', signal_data)
