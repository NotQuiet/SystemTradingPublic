import gspread
import asyncio
from Scripts.Tests.TestBinanceToken import BinanceTokenValidator
from google.oauth2.service_account import Credentials
from concurrent.futures import ThreadPoolExecutor

class GoogleSheetsController:
    tokensValidator: BinanceTokenValidator

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self):
        self.tokensValidator = BinanceTokenValidator()
        self.spreadsheet = None
        self.client = None
        self.createClient()

    def createClient(self):
        creds = Credentials.from_service_account_file('C:/Users/Mikhail/Desktop/cryptoboysband-4a790a8ea387.json',
                                                      scopes=self.scopes)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open("CryptoBoysBand configuration")

    async def getActiveIntervals(self):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            data = await loop.run_in_executor(
                pool, self._fetch_active_intervals_data
            )
        return data

    async def getActiveTokens(self):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            data = await loop.run_in_executor(
                pool, self._fetch_active_tokens_data
            )
        validated_data = await self.tokensValidator.validate_tokens(data)
        return validated_data

    def _fetch_active_tokens_data(self):
        worksheet = self.spreadsheet.worksheet('TokensInUse')
        return worksheet.get_all_values()

    def _fetch_active_intervals_data(self):
        worksheet = self.spreadsheet.worksheet('ActiveIntervals')
        return worksheet.get_all_values()
