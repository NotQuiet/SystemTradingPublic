import json
from Scripts.Dto.ClientDataDto import ClientDataDto

class JsonParser:
    def ParseClientData(self, data: str) -> ClientDataDto:
        return json.loads(data)