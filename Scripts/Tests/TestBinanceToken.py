import aiohttp
import asyncio

class BinanceTokenValidator:

    async def fetch_exchange_info(self):
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def validate_tokens(self, tokens):
        data = await self.fetch_exchange_info()

        valid_symbols = set(s['symbol'] for s in data['symbols'])

        # Удаляем токены со значением 'FALSE'
        tokens = [token_list for token_list in tokens if token_list[1].upper() != 'FALSE']

        # Оставляем только валидные токены и устанавливаем значение 'TRUE' для каждого
        validated_tokens = [
            [token_list[0], 'TRUE']
            for token_list in tokens
            if token_list[0].upper() in valid_symbols
        ]


        return validated_tokens


