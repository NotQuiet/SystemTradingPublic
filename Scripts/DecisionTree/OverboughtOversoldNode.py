from Scripts.DecisionTree.TreeNode import Node
from Scripts.Dto.IncomeTreeDataDto import IncomeTreeDataDto

class OverboughtOversoldNode(Node):
    def analyze(self, data: IncomeTreeDataDto):
        if data.overbought and data.volume > 1500:
            result = "overbought"
        elif data.oversold and data.volume > 1500:
            result = "oversold"
        else:
            result = "neutral"
        print(f"{self.name} detected {result}.")
        return result
