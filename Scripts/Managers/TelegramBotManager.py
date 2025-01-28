from telegram.helpers import escape_markdown
from telegram.request import HTTPXRequest
from Scripts.TelegramBot.DefaultTelegramBot import TelegramBot
import re

class TelegramBotManager:
    def __init__(self):
        trequest = HTTPXRequest(connection_pool_size=20)
        self.telegram_bot = TelegramBot(HTTPXRequest(connection_pool_size=20))

    async def send_message_to_dev_group(self, message: str):
        await self.telegram_bot.sendMessage(escape_markdown(message))

    async def send_message_to_prod_group(self, message: str):
        await self.telegram_bot.send_message_to_smart_roi_chat(escape_markdown(message))

    async def send_message_to_breakdown_group(self, message: str):
        await self.telegram_bot.send_message_to_breakdown_chat(escape_markdown(message))

    def escape_markdown(self, text):
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

