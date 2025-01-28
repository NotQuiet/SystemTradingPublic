from Scripts.Dto.IncomeTreeDataDto import IncomeTreeDataDto

class Node:
    ignore_time_frames = {}

    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def set_ignore_time_frames(self, ignore_time_frames):
        self.ignore_time_frames = ignore_time_frames


    async def analyze(self, data: dict, interval: str):
        print(f"node analyze {self.name}")
        raise NotImplementedError("Subclasses should implement this!")