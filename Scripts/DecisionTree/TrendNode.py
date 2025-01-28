from Scripts.DecisionTree.TreeNode import Node
from Scripts.Dto.IncomeTreeDataDto import IncomeTreeDataDto

class TrendNode(Node):
    def analyze(self, data: IncomeTreeDataDto):
        trend = "upward" if data.currentPrice > data.lastPrice else "downward"
        print(f"{self.name} detected {trend} trend.")
        return trend