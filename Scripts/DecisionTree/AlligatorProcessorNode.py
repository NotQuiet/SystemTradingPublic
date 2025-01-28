import pandas as pd
import asyncio

from Scripts.DecisionTree.TreeNode import Node
from Scripts.DecisionTree.Signals.SignalManager import SignalManager

class AlligatorProcessorNode(Node):

    def __init__(self, name, signal_manager: SignalManager):
        super().__init__(name)
        self.signal_manager = signal_manager
        self.previous_states = {}

    async def analyze(self, prices_dict: dict, interval: str):
        if interval in self.ignore_time_frames:
            return
        self.interval = interval
        tasks = [
            self.detect_crossovers(tokenPair, data['prices'])
            for tokenPair, data in prices_dict.items()
        ]
        await asyncio.gather(*tasks)
        print(f"---   {self.name} node analyze process completed for all token pairs.")

    async def smma(self, src, length):
        smma_values = [0] * len(src)
        smma_values[0] = src[0]
        for i in range(1, len(src)):
            smma_values[i] = (smma_values[i - 1] * (length - 1) + src[i]) / length
        return smma_values

    async def detect_crossovers(self, tokenPair, prices):
        jaw_length = 13
        teeth_length = 8
        lips_length = 5
        jaw_offset = 8
        teeth_offset = 5
        lips_offset = 3

        jaw = await self.smma(prices, jaw_length)
        teeth = await self.smma(prices, teeth_length)
        lips = await self.smma(prices, lips_length)

        jaw = pd.Series(jaw).shift(jaw_offset).tolist()
        teeth = pd.Series(teeth).shift(teeth_offset).tolist()
        lips = pd.Series(lips).shift(lips_offset).tolist()

        current_state = self.get_current_state(jaw[-1], teeth[-1], lips[-1])

        previous_state = self.previous_states.get(tokenPair)

        if previous_state is not None and previous_state != current_state:
            await self.on_alligator_change(tokenPair, current_state)

        self.previous_states[tokenPair] = current_state


    def get_current_state(self, jaw, teeth, lips):
        if lips > teeth > jaw:
            return 'uptrend'
        elif lips < teeth < jaw:
            return 'downtrend'
        else:
            return 'sleeping'

    async def on_alligator_change(self, tokenPair, current_state):
        signal_data = {
            'state': current_state
        }
        await self.signal_manager.process_signal(tokenPair, self.interval, 'Alligator', signal_data)
        print(f"Alligator изменился для {tokenPair} на интервале {self.interval}: {current_state}")
