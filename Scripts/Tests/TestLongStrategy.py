import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone

from Scripts.DecisionTree.DecisionTree import DecisionTree
from Scripts.DecisionTree.RsiProcessorNode import RsiProcessorNode
from Scripts.DecisionTree.NadarayaWatsonEnvelopeNode import NadarayaWatsonEnvelope
from Scripts.Managers.TelegramBotManager import TelegramBotManager
from Scripts.DecisionTree.NodeAnalyze.RsiEnvelopeAlertManager import RsiEnvelopeAlertManager
from Scripts.DecisionTree.Transactions.TransactionsManager import TransactionManager


class HistoricalBacktest:
    def __init__(self, symbols):
        self.symbols = symbols
        self.transaction_manager = TransactionManager()
        self.decision_tree = self._setup_decision_tree()
        self.historical_data = {}

    def _setup_decision_tree(self):
        rsi_envelope_alert_manager = RsiEnvelopeAlertManager(transaction_manager=self.transaction_manager)
        rsi_processor_node = RsiProcessorNode("RsiProcessorNode", alert_manager=rsi_envelope_alert_manager)
        envelope_processor_node = NadarayaWatsonEnvelope("NadarayaWatsonEnvelope",
                                                         alert_manager=rsi_envelope_alert_manager)
        rsi_processor_node.add_child(envelope_processor_node)

        decision_tree = DecisionTree()
        decision_tree.set_root(rsi_processor_node)
        return decision_tree

    async def fetch_historical_data(self, session, symbol, start_time, interval='5m'):
        end_time = datetime.now(timezone.utc)
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={int(start_time.timestamp() * 1000)}&endTime={int(end_time.timestamp() * 1000)}&limit=1000"
        async with session.get(url) as response:
            data = await response.json()
            if isinstance(data, list) and len(data) > 0:
                return [float(candle[4]) for candle in data]  # Закрывающие цены
            else:
                return []

    async def load_historical_data(self):
        start_time = datetime.now(timezone.utc) - timedelta(days=180)  # Полгода назад
        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol in self.symbols:
                tasks.append(self.fetch_historical_data(session, symbol, start_time))
            results = await asyncio.gather(*tasks)

            for i, symbol in enumerate(self.symbols):
                if results[i]:
                    self.historical_data[symbol] = results[i]
                else:
                    print(f"⚠️ Нет данных для символа {symbol} за указанный период.")

    async def run_backtest(self):
        await self.load_historical_data()

        for symbol in self.symbols:
            if symbol in self.historical_data:
                data_chunks = [self.historical_data[symbol][i:i + 500] for i in
                               range(0, len(self.historical_data[symbol]), 500)]
                for chunk in data_chunks:
                    await self.decision_tree.analyze({symbol: chunk}, '5m')

    def save_transactions(self):
        self.transaction_manager.save_transactions()


async def main():
    symbols = ['BTCUSDT', 'UNFIUSDT', 'GALAUSDT', 'LPTUSDT', 'RAREUSDT', 'VOXELUSDT',
               'NOTUSDT', 'MEMEUSDT', 'LISTAUSDT', 'TNSRUSDT', 'ENSUSDT', 'HOOKUSDT', 'REEFUSDT']
    backtest = HistoricalBacktest(symbols)
    await backtest.run_backtest()
    backtest.save_transactions()


if __name__ == "__main__":
    asyncio.run(main())
