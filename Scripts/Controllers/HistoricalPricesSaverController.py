class HistoricalPricesSaverController:
    file_path = "prices.txt"
    def save_prices_to_file(self, prices: []):

        with open(self.file_path, 'w') as f:
            for price in prices:
                f.write(f"{price}\n")