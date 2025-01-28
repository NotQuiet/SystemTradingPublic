import asyncio
import time

class SignalRepository:
    def __init__(self):
        self.signals = {}  # Ключ: (symbol, interval, signal_type), значение: {'data': ..., 'timestamp': ..., 'expiration_time': ...}
        self.lock = asyncio.Lock()

    async def add_signal(self, symbol, interval, signal_type, signal_data, ttl):
        async with self.lock:
            key = (symbol, interval, signal_type)
            expiration_time = time.time() + ttl
            self.signals[key] = {
                'data': signal_data,
                'timestamp': time.time(),
                'expiration_time': expiration_time
            }

    async def get_signal(self, symbol, interval, signal_type):
        async with self.lock:
            signal = self.signals.get((symbol, interval, signal_type))
            if signal and signal['expiration_time'] >= time.time():
                return signal
            else:
                if signal:
                    del self.signals[(symbol, interval, signal_type)]
                return None

    async def remove_signal(self, symbol, interval, signal_type):
        async with self.lock:
            key = (symbol, interval, signal_type)
            if key in self.signals:
                del self.signals[key]

    async def clean_up_signals(self):
        async with self.lock:
            current_time = time.time()
            keys_to_delete = [
                key for key, value in self.signals.items()
                if value['expiration_time'] < current_time
            ]
            for key in keys_to_delete:
                del self.signals[key]
