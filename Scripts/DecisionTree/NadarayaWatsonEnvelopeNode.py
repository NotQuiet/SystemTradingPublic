import numpy as np
import pandas as pd

from Scripts.DecisionTree.TreeNode import Node
from Scripts.DecisionTree.Signals.SignalManager import SignalManager


class NadarayaWatsonEnvelope(Node):

    def __init__(self, name, signal_manager: SignalManager, h=8.0, mult=3.0, repaint=True, visualize=False):
        super().__init__(name)
        self.interval = "0m"
        self.h = h
        self.mult = mult
        self.repaint = repaint
        self.visualize = visualize
        self.previous_bounds = {}
        self.crossing_state = {}
        self.signal_manager = signal_manager

    def gauss(self, x):
        return np.exp(-(x ** 2) / (2 * self.h ** 2))

    def compute_coefficients(self, length):
        coefs = np.array([self.gauss(i) for i in range(length)])
        return coefs, np.sum(coefs)

    def compute_smoothing(self, src):
        coefs, den = self.compute_coefficients(len(src))
        out = np.convolve(src, coefs[::-1], mode='same') / den
        mae = pd.Series(np.abs(src - out)).rolling(500).mean().fillna(0).values * self.mult
        return out, mae

    def compute_envelope(self, src):
        if self.repaint:
            return self.compute_envelope_repainting(src)
        else:
            return self.compute_smoothing(src)

    def compute_envelope_repainting(self, src):
        envelope = np.zeros(len(src))
        sae = 0.0

        for i in range(len(src)):
            sum_weights = 0.0
            weighted_sum = 0.0
            for j in range(len(src)):
                weight = self.gauss(i - j)
                weighted_sum += src[j] * weight
                sum_weights += weight

            envelope[i] = weighted_sum / sum_weights if sum_weights != 0 else src[i]
            sae += abs(src[i] - envelope[i])

        sae *= self.mult / len(src)
        return envelope, sae

    async def analyze(self, prices_dict: dict, interval: str):
        if interval in self.ignore_time_frames:
            return
        self.interval = interval
        for tokenPair, data in prices_dict.items():
            prices = data['prices']
            await self.calculate(tokenPair, prices)
        print(f"---   {self.name} node analyze process completed for all token pairs.")

    async def calculate(self, tokenPair, prices):
        envelope, mae = self.compute_envelope(prices)
        upper_bound = envelope + mae
        lower_bound = envelope - mae

        if tokenPair not in self.crossing_state:
            self.crossing_state[tokenPair] = {'above': False, 'below': False}

        state = self.crossing_state[tokenPair]

        last_upper_bound = upper_bound[-1]
        last_lower_bound = lower_bound[-1]

        last_price = prices[-1]

        if last_price > last_upper_bound and not state['above']:
            await self.on_upper_bound(tokenPair)
            state['above'] = True
        elif last_price <= last_upper_bound:
            state['above'] = False

        if last_price < last_lower_bound and not state['below']:
            await self.on_lower_bound(tokenPair)
            state['below'] = True
        elif last_price >= last_lower_bound:
            state['below'] = False

        if self.visualize:
            self.plot_envelope(prices, envelope, upper_bound, lower_bound)

    def plot_envelope(self, src, envelope, upper_bound, lower_bound):
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 6))
        plt.plot(src, label='Source')
        plt.plot(envelope, label='Envelope')
        plt.plot(upper_bound, label='Upper Bound', linestyle='--', color='green')
        plt.plot(lower_bound, label='Lower Bound', linestyle='--', color='red')
        plt.fill_between(range(len(src)), upper_bound, lower_bound, color='gray', alpha=0.2)
        plt.legend()
        plt.show()

    async def on_upper_bound(self, tokenPair):
        signal_data = {
            'direction': 'cross_up'
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'Envelope', signal_data)

    async def on_lower_bound(self, tokenPair):
        signal_data = {
            'direction': 'cross_down'
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'Envelope', signal_data)
