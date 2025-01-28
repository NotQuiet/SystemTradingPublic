import asyncio
import traceback
from datetime import datetime, timedelta, timezone

import aiohttp

from Scripts.Controllers.DecisionTreeController import DecisionTreeController
from Scripts.Controllers.GoogleSheetsController import GoogleSheetsController
from binance.client import Client


class BinanceSocketController:
    symbols = []
    intervals = []

    decisionTreeController: DecisionTreeController
    googleSheetController: GoogleSheetsController

    # Запуск сокета через контроллер

    def __init__(self, client: Client):
        self.createDecisionTree(client)
        self.createGoogleSheetController()
        asyncio.run(self.setSymbols())
        asyncio.run(self.setIntervals())

        asyncio.run(self.startInfinityLoop())

    async def setSymbols(self):
        data = await self.googleSheetController.getActiveTokens()
        for symbol in data:
            if symbol[1].upper() == 'TRUE':
                self.symbols.append(symbol[0])

    async def updateSymbols(self):
        self.symbols = []
        data = await self.googleSheetController.getActiveTokens()
        for symbol in data:
            if symbol[1].upper() == 'TRUE':
                self.symbols.append(symbol[0])

    async def setIntervals(self):
        data = await self.googleSheetController.getActiveIntervals()
        for interval in data:
            if interval[1].upper() == 'TRUE':
                self.intervals.append(interval[0])

    async def updateIntervals(self):
        self.intervals = []
        data = await self.googleSheetController.getActiveIntervals()
        for interval in data:
            if interval[1].upper() == 'TRUE':
                self.intervals.append(interval[0])


    async def startInfinityLoop(self):
        while True:
            try:
                for interval in self.intervals:
                    await self.loadHistoricalIntervalPrices(interval)
                    await self.decisionTreeController.analyzeTree(interval)

                await self.updateSymbols()
                await self.updateIntervals()

            except aiohttp.ClientError as e:
                print(f"Client error: {e}")
            except asyncio.TimeoutError:
                print("Timeout error")
            except Exception as e:
                print(f"Unexpected error: {e}")
                traceback.print_exc()

            await asyncio.sleep(10)

    def createDecisionTree(self, client: Client):
        self.decisionTreeController = DecisionTreeController(client)

    def createGoogleSheetController(self):
        self.googleSheetController = GoogleSheetsController()


    async def loadHistoricalIntervalPrices(self, interval):
        timeout = aiohttp.ClientTimeout(total=5)  # Таймаут в 5 секунд
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                await self.decisionTreeController.load_historical_interval_prices(
                    symbols=self.symbols, interval=interval, session=session
                )
            except aiohttp.ClientConnectorError as e:
                print(f"Ошибка подключения: {e}")
            except aiohttp.ClientResponseError as e:
                print(f"Ошибка ответа от сервера: {e}")
            except asyncio.TimeoutError:
                print("Таймаут запроса")
            except Exception as e:
                print(f"Произошла непредвиденная ошибка: {e}")
                traceback.print_exc()

    async def startTestOnHalfYear(self):
        historical_data = {}

        # Загружаем данные для всех символов
        for symbol in self.symbols:
            data = await self.fetch_historical_data_for_half_year(symbol)
            if data:
                historical_data[symbol] = data
            else:
                print(f"Пропускаю символ {symbol}, так как нет данных.")

        # Разделяем данные на куски и передаем их для анализа
        historical_chunks = {}
        for symbol, data in historical_data.items():
            historical_chunks[symbol] = self.create_test_chunks(data)

        # Прогоняем каждый кусок через анализатор
        for i in range(len(next(iter(historical_chunks.values())))):
            chunk_data = {symbol: chunks[i] for symbol, chunks in historical_chunks.items() if i < len(chunks)}
            await self.decisionTreeController.testAnalyzeTree(chunk_data, "1m")

    async def fetch_historical_data_for_half_year(self, symbol: str, interval: str = '1m'):
        start_time = datetime.now(timezone.utc) - timedelta(days=1)
        end_time = datetime.now(timezone.utc)
        historical_data = []

        async with aiohttp.ClientSession() as session:
            while start_time < end_time:
                url = (
                    f"https://api.binance.com/api/v3/klines?"
                    f"symbol={symbol}&interval={interval}"
                    f"&startTime={int(start_time.timestamp() * 1000)}"
                    f"&endTime={int(end_time.timestamp() * 1000)}"
                    f"&limit=1000"
                )
                async with session.get(url) as response:
                    data = await response.json()

                    # Проверяем, вернулись ли данные корректно
                    if not isinstance(data, list) or len(data) == 0:
                        print(f"⚠️ Нет данных или ошибка при запросе для символа {symbol}")
                        break

                    try:
                        for candle in data:
                            close_price = float(candle[4])
                            historical_data.append(close_price)
                    except (IndexError, ValueError, TypeError) as e:
                        print(f"⚠️ Пропущена некорректная свеча для символа {symbol}: {candle} - Ошибка: {e}")
                        continue

                    start_time = datetime.utcfromtimestamp(data[-1][6] / 1000).replace(tzinfo=timezone.utc) + timedelta(
                        minutes=5)

                    # Если вернулось меньше 1000 свечей, значит данные закончились
                    if len(data) < 1000:
                        break

        return historical_data

    def create_test_chunks(self, data, chunk_size=500, step=10):
        chunks = []
        for i in range(0, len(data) - chunk_size + 1, step):
            chunk = data[i:i + chunk_size]
            chunks.append(chunk)
        return chunks
