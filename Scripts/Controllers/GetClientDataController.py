from binance.client import Client


from Scripts.Dto.ClientDataDto import ClientDataDto
from Scripts.Controllers.JsonParserController import JsonParser

class ClientDataController:

        client: Client

        def __init__(self, client: Client):
            self.client = client

        def GetClientData(self)->ClientDataDto:
            return ClientDataDto.from_dict(self.client.get_account())

   
