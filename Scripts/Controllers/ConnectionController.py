import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from binance.client import Client
from Scripts.Managers.ConnectionManager import ConnectionManager
from Scripts.Constants.ApiInfo import ApiInfo

def main():
    api_info = ApiInfo()

    client = Client(api_info.api_key, api_info.api_secret)

    # Проверка работы API
    try:
        connection_manager = ConnectionManager(client)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()



if __name__ == "__main__":
    main()
