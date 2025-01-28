from Scripts.DecisionTree.TreeNode import Node
from Scripts.Dto.IncomeTreeDataDto import IncomeTreeDataDto
from binance.client import Client


class DecisionTree:
    def __init__(self):
        self.root = None

    def set_root(self, node: Node):
        self.root = node

    async def analyze(self, data: {}, interval: str):
        if not self.root:
            raise ValueError("The root node is not set.")
        await self._recursive_analyze(self.root, data, interval)

    async def _recursive_analyze(self, node: Node, data: dict, interval: str):
        result = await node.analyze(data, interval)
        for child in node.children:
            await self._recursive_analyze(child, data, interval)
