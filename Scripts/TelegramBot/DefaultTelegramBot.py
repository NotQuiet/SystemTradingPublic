import asyncio
from telegram.request import HTTPXRequest
from telegram import Bot
from Scripts.Constants.ApiInfo import ApiInfo

class TelegramBot:
    def __init__(self, trequest: HTTPXRequest):
        self.apiInfo = ApiInfo()
        self.token = self.apiInfo.telegram_token
        self.CHAT_ID = self.apiInfo.telegram_chat_id
        self.smart_roi_chat_id = self.apiInfo.smart_roi_telegram_chat_id
        self.breakdown_chat_id = self.apiInfo.channel_breakdown_telegram_chat_id
        self.bot = Bot(token=self.token, request=trequest)

    def connectBot(self):
        bot = TelegramBot()

    async def errere(self):
        await self.bot.getUpdates()

    async def sendMessage(self, message: str):
        await self.processMessage(message, self.CHAT_ID)

    async def send_message_to_smart_roi_chat(self, message: str):
        await self.processMessage(message, self.smart_roi_chat_id)

    async def send_message_to_breakdown_chat(self, message: str):
        await self.processMessage(message, self.breakdown_chat_id)

    async def processMessage(self, message, chat_id=None):
        try:
            await self.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        except Exception as e:
            await asyncio.sleep(0)
            print(f"Ошибка при отправке сообщения: {e}")



