import json
from datetime import datetime
from binance.client import Client
from binance.error import ClientError
from Scripts.DecisionTree.Transactions.Transaction import Transaction
from Scripts.Managers.TelegramBotManager import TelegramBotManager

class TransactionManager:
    def __init__(self, cm_client: Client, transaction_file='transactions.json'):
        self.transactions = []
        self.transaction_file = transaction_file
        self.client = cm_client
        self.load_transactions()
        self.telegram_bot_manager = TelegramBotManager()

    async def open_position(self, symbol, interval, direction):
        existing_transaction = self.get_active_transaction_by_symbol_and_interval(symbol, interval)
        if existing_transaction:
            print(f"Сделка по {symbol} на интервале {interval} уже открыта и активна, пропускаем создание новой сделки.")
            return

        try:
            price_data = self.client.futures_mark_price(symbol=symbol)
            entry_price = float(price_data['markPrice'])
        except ClientError as e:
            print(f"Ошибка при получении цены для {symbol}: {e}")
            return

        if direction == "long":
            stop_loss = entry_price * (1 - 0.001)
        elif direction == "short":
            stop_loss = entry_price * (1 + 0.001)
        else:
            print(f"Неверное направление сделки: {direction}")
            return

        transaction = Transaction(symbol, entry_price, direction, stop_loss, take_profit=None, interval=interval)

        transaction.highest_price = entry_price if direction == "long" else None
        transaction.lowest_price = entry_price if direction == "short" else None

        self.transactions.append(transaction)
        self.save_transactions()

        await self.open_order_on_binance(symbol, entry_price, direction)

        await self.send_transaction_notification(transaction, "🚀 Открыта сделка")

    async def close_position(self, symbol, interval):
        transaction = self.get_active_transaction_by_symbol_and_interval(symbol, interval)
        if not transaction:
            return

        try:
            price_data = self.client.futures_mark_price(symbol=symbol)
            exit_price = float(price_data['markPrice'])
        except ClientError as e:
            print(f"Ошибка при получении цены для {symbol}: {e}")
            return

        # Закрываем сделку
        transaction.exit_price = exit_price
        transaction.active = False

        # Рассчитываем прибыль/убыток
        self.calculate_profit_loss(transaction)
        self.save_transactions()

        # Закрываем ордер на Binance
        await self.close_order_on_binance(symbol, exit_price, transaction.direction)

        await self.send_transaction_notification(transaction, "💼 Закрыта сделка")

    def get_active_transaction_by_symbol_and_interval(self, symbol, interval):
        for transaction in self.transactions:
            if transaction.symbol == symbol and transaction.interval == interval and transaction.active:
                return transaction
        return None

    def calculate_profit_loss(self, transaction):
        if transaction.exit_price is not None:
            if transaction.direction == "long":
                transaction.profit_loss_percentage = (
                    ((transaction.exit_price - transaction.entry_price) / transaction.entry_price) * 100)
            elif transaction.direction == "short":
                transaction.profit_loss_percentage = (
                    ((transaction.entry_price - transaction.exit_price) / transaction.entry_price) * 100)

    async def open_order_on_binance(self, symbol, price, direction, quantity=None):
        order_side = 'BUY' if direction == "long" else 'SELL'

        try:
            symbol = symbol.upper()
            precision_info = self.get_symbol_precision(symbol)
            if precision_info is None:
                raise ValueError(f"Не удалось получить информацию о точности для символа {symbol}")

            quantity_precision = precision_info['quantity_precision']

            min_notional = 20.0

            if quantity is None:
                quantity = min_notional / price
            else:
                quantity = float(quantity)

            quantity = round(quantity, quantity_precision)

            notional = quantity * price

            if notional < min_notional:
                quantity += 10 ** (-quantity_precision)
                quantity = round(quantity, quantity_precision)
                notional = quantity * price

                if notional < min_notional:
                    print(f"Ошибка: не удалось рассчитать количество для {symbol}, чтобы достичь минимального значения {min_notional} USDT.")
                    return

            if quantity <= 0:
                print(f"Ошибка: рассчитанное количество для {symbol} меньше или равно 0 ({quantity}). Ордер не может быть создан.")
                return

            order = self.client.futures_create_order(
                symbol=symbol,
                side=order_side,
                type='MARKET',  # Рыночный ордер
                quantity=quantity
            )
            print(f"Открыт рыночный ордер на {order_side} {symbol} с количеством {quantity}")
            await self.send_default_telegram_notification(
                f"Открыт рыночный ордер на {order_side} {symbol} с количеством {quantity}")

        except ClientError as e:
            await self.send_default_telegram_notification(f"Ошибка при открытии ордера {symbol}: {e}")
            print(f"Ошибка при открытии ордера: {e}")

    async def close_order_on_binance(self, symbol, price, direction):
        order_side = 'SELL' if direction == "long" else 'BUY'

        try:
            precision_info = self.get_symbol_precision(symbol)
            if precision_info is None:
                raise ValueError(f"Не удалось получить информацию о точности для символа {symbol}")

            quantity_precision = precision_info['quantity_precision']

            positions = self.client.futures_position_information(symbol=symbol)

            quantity = 0
            for position in positions:
                if position['symbol'] == symbol:
                    quantity = abs(float(position['positionAmt']))
                    break

            if quantity > 0:
                quantity = round(quantity, quantity_precision)

                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=order_side,
                    type='MARKET',  # Рыночный ордер
                    quantity=quantity
                )
                print(f"Закрыт рыночный ордер на {order_side} {symbol} с количеством {quantity}")
                await self.send_default_telegram_notification(
                    f"Закрыт рыночный ордер на {order_side} {symbol} с количеством {quantity}")
            else:
                print(f"Нет доступной позиции для закрытия по {symbol}.")
                await self.send_default_telegram_notification(f"Нет доступной позиции для закрытия по {symbol}")

        except ClientError as e:
            print(f"Ошибка при закрытии ордера: {e}")
            await self.send_default_telegram_notification(f"Ошибка при закрытии ордера: {e}")

    async def monitor_transactions(self, current_prices, interval):
        for transaction in self.transactions:
            if transaction.active and transaction.interval == interval:
                symbol = transaction.symbol
                current_price = current_prices.get(symbol)
                if current_price is None:
                    continue

                print(f"Мониторинг {symbol}: текущая цена {current_price}, стоп-лосс {transaction.stop_loss}")

                if transaction.direction == "long":
                    if current_price > (transaction.highest_price or transaction.entry_price):
                        transaction.highest_price = current_price
                        transaction.stop_loss = current_price * (1 - 0.001)
                        print(f"Обновляем стоп-лосс для {symbol}: {transaction.stop_loss}")
                        self.save_transactions()
                    elif current_price <= transaction.stop_loss:
                        print(f"Цена упала ниже стоп-лосса для {symbol}. Закрываем сделку.")
                        await self.close_position(symbol, transaction.interval)

                elif transaction.direction == "short":
                    if current_price < (transaction.lowest_price or transaction.entry_price):
                        transaction.lowest_price = current_price
                        transaction.stop_loss = current_price * (1 + 0.001)
                        print(f"Обновляем стоп-лосс для {symbol}: {transaction.stop_loss}")
                        self.save_transactions()
                    elif current_price >= transaction.stop_loss:
                        print(f"Цена поднялась выше стоп-лосса для {symbol}. Закрываем сделку.")
                        await self.close_position(symbol, transaction.interval)

    def get_symbol_precision(self, symbol):
        exchange_info = self.client.futures_exchange_info()
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                return {
                    'price_precision': symbol_info['pricePrecision'],
                    'quantity_precision': symbol_info['quantityPrecision']
                }
        return None

    def save_transactions(self):
        with open(self.transaction_file, 'w') as f:
            transactions_data = []
            for transaction in self.transactions:
                transaction_data = transaction.__dict__.copy()
                if isinstance(transaction_data.get('created_at'), datetime):
                    transaction_data['created_at'] = transaction_data['created_at'].isoformat()
                if isinstance(transaction_data.get('updated_at'), datetime):
                    transaction_data['updated_at'] = transaction_data['updated_at'].isoformat()
                transactions_data.append(transaction_data)
            json.dump(transactions_data, f, indent=4)

    def load_transactions(self):
        try:
            with open(self.transaction_file, 'r') as f:
                transaction_dicts = json.load(f)
                for transaction_dict in transaction_dicts:
                    if 'created_at' in transaction_dict and transaction_dict['created_at']:
                        transaction_dict['created_at'] = datetime.fromisoformat(transaction_dict['created_at'])
                    if 'updated_at' in transaction_dict and transaction_dict['updated_at']:
                        transaction_dict['updated_at'] = datetime.fromisoformat(transaction_dict['updated_at'])
                    transaction = Transaction(
                        transaction_dict['symbol'],
                        transaction_dict['entry_price'],
                        transaction_dict['direction'],
                        transaction_dict['stop_loss'],
                        transaction_dict.get('take_profit'),
                        transaction_dict.get('interval')
                    )
                    transaction.id = transaction_dict['id']
                    transaction.exit_price = transaction_dict['exit_price']
                    transaction.profit_loss_percentage = transaction_dict['profit_loss_percentage']
                    transaction.active = transaction_dict['active']
                    transaction.highest_price = transaction_dict.get('highest_price')
                    transaction.lowest_price = transaction_dict.get('lowest_price')
                    self.transactions.append(transaction)
        except FileNotFoundError:
            self.transactions = []

    async def send_transaction_notification(self, transaction, message_prefix):
        profit_loss_info = f"{transaction.profit_loss_percentage:.2f}%" if transaction.profit_loss_percentage is not None else "не рассчитано"
        message = (f"{message_prefix} для {transaction.symbol}:\n"
                   f"Тип сделки: {transaction.direction.upper()}\n"
                   f"Цена входа: {transaction.entry_price}\n"
                   f"Цена выхода: {transaction.exit_price if transaction.exit_price else 'не установлена'}\n"
                   f"Прибыль/Убыток: {profit_loss_info}\n"
                   f"Интервал: {transaction.interval}")

        print(message)

    async def send_default_telegram_notification(self, message):
        return
