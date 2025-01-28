import asyncio
import aiohttp
from binance.client import Client

from Scripts.DecisionTree.DecisionTree import DecisionTree
from Scripts.DecisionTree.RsiProcessorNode import RsiProcessorNode
from Scripts.DecisionTree.NadarayaWatsonEnvelopeNode import NadarayaWatsonEnvelope
from Scripts.DecisionTree.MACDTradeNode import MACDTradeNode
from Scripts.Controllers.HistoricalPricesSaverController import HistoricalPricesSaverController
from Scripts.DecisionTree.NodeAnalyze.RsiEnvelopeAlertManager import RsiEnvelopeAlertManager
from Scripts.DecisionTree.Transactions.TransactionsManager import TransactionManager
from Scripts.DecisionTree.AlligatorProcessorNode import AlligatorProcessorNode
from Scripts.DecisionTree.MACDProcessorNode import MACDProcessorNode
from Scripts.DecisionTree.PumpDumpDetectorNode import PumpDumpDetectorNode
from Scripts.DecisionTree.NodeAnalyze.MACDAlertManager import MACDAlertManager
from Scripts.DecisionTree.NodeAnalyze.PumpDumpAlertManager import PumpDumpAlertManager
from Scripts.DecisionTree.OpenInterestProcessorNode import OpenInterestProcessorNode  # Добавьте этот импорт
from Scripts.DecisionTree.NodeAnalyze.OpenInterestAlertManager import OpenInterestAlertManager  # Добавьте этот импорт
from Scripts.DecisionTree.Signals.SignalRepository import SignalRepository
from Scripts.DecisionTree.Signals.SignalManager import SignalManager


class DecisionTreeController:

    prices = []
    historical_data = {}
    tokenPair: str = ""

    def __init__(self, client: Client):
        self.client = client
        self.transactionManager = None
        self.decision_tree = None
        self.envelopeProcessorNode = None
        self.rsiProcessorNode = None
        self.macd_trade_node = None
        self.alligatorProcessorNode = None
        self.macdProcessorNode = None
        self.rsi_envelope_alert_manager = None
        self.macd_alert_manager = None
        self.pump_dump_detector_node = None
        self.pump_dump_alert_manager = None
        self.open_interest_processor_node = None
        self.open_interest_alert_manager = None
        self.historicalPriceSaverController = HistoricalPricesSaverController()
        asyncio.run(self.setNodes(client))

    async def setNodes(self, client: Client):
        self.transactionManager = TransactionManager(client)

        self.signal_manager = SignalManager()
        await self.signal_manager.start_periodic_clean_up()

        self.macd_alert_manager = MACDAlertManager(transaction_manager=self.transactionManager)
        self.rsi_envelope_alert_manager = RsiEnvelopeAlertManager(transaction_manager=self.transactionManager)
        self.pump_dump_alert_manager = PumpDumpAlertManager(transaction_manager=self.transactionManager)
        self.open_interest_alert_manager = OpenInterestAlertManager()

        self.rsiProcessorNode = RsiProcessorNode(signal_manager=self.signal_manager, name="RsiProcessorNode")
        self.macd_trade_node = MACDTradeNode(name="MACDTradeNode", transaction_manager=self.transactionManager)
        self.envelopeProcessorNode = NadarayaWatsonEnvelope(signal_manager=self.signal_manager, name="NadarayaWatsonEnvelope")
        self.alligatorProcessorNode = AlligatorProcessorNode(signal_manager=self.signal_manager, name="Alligator")
        self.macdProcessorNode = MACDProcessorNode(signal_manager=self.signal_manager, name="MACD")
        self.pump_dump_detector_node = PumpDumpDetectorNode(signal_manager=self.signal_manager, name="PumpDumpDetectorNode")
        self.open_interest_processor_node = OpenInterestProcessorNode(signal_manager=self.signal_manager, name="OpenInterestProcessorNode")

        self.set_block_timeframes()

        # Устанавливаем связи между нодами
        self.rsiProcessorNode.add_child(self.envelopeProcessorNode)
        self.rsiProcessorNode.add_child(self.rsiProcessorNode)
        self.rsiProcessorNode.add_child(self.open_interest_processor_node)

        self.decision_tree = DecisionTree()
        self.decision_tree.set_root(self.rsiProcessorNode)


    def set_block_timeframes(self):
        self.rsiProcessorNode.set_ignore_time_frames({"1m"})
        self.envelopeProcessorNode.set_ignore_time_frames({"1m"})
        self.alligatorProcessorNode.set_ignore_time_frames({"1m"})
        self.macdProcessorNode.set_ignore_time_frames({"15m"})
        self.pump_dump_detector_node.set_ignore_time_frames({"1m"})
        self.open_interest_processor_node.set_ignore_time_frames({"1m"})
        self.macd_trade_node.set_ignore_time_frames({"1m", "15m"})

    async def fetch_historical_data(self, session, symbol, interval):
        # Получение исторических цен
        url_prices = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=500"
        async with session.get(url_prices) as response_prices:
            data_prices = await response_prices.json()

            prices = [float(candle[4]) for candle in data_prices if len(candle) > 4]

        # Получение исторических данных об открытом интересе
        url_oi = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period={interval}&limit=500"
        async with session.get(url_oi) as response_oi:
            data_oi = await response_oi.json()
            open_interest = [float(item['sumOpenInterestValue']) for item in data_oi]


        # Убедимся, что длина списков совпадает
        min_length = min(len(prices), len(open_interest))
        prices = prices[-min_length:]
        open_interest = open_interest[-min_length:]

        return symbol, prices, open_interest

    async def fetch_current_price(self, symbol):
        response = self.client.futures_mark_price(symbol=symbol)
        return float(response['markPrice'])

    async def load_historical_interval_prices(self, symbols, interval, session):
        async with session:
            tasks = [self.fetch_historical_data(session, symbol.upper(), interval) for symbol in symbols]

            results = await asyncio.gather(*tasks)

            for symbol, prices, open_interest in results:
                current_price = await self.fetch_current_price(symbol)
                print(f'Last price {symbol} - {current_price}')# Получаем текущую цену
                prices[-1] = current_price  # Заменяем последнее значение на текущую цену
                self.historical_data[symbol] = {
                    'prices': prices,
                    'open_interest': open_interest
                }


                # Передаем данные в TransactionManager для мониторинга, для системного трейдинга
                await self.transactionManager.monitor_transactions({symbol: prices[-1]}, interval)

            return self.historical_data

    async def analyzeTree(self, interval: str):
        await self.decision_tree.analyze(self.historical_data, interval)
