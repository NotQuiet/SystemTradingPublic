from Scripts.DecisionTree.TreeNode import Node
from Scripts.Dto.IncomeTreeDataDto import IncomeTreeDataDto

class VolumeNode(Node):
    def analyze(self, data: IncomeTreeDataDto):
        if data.volume > 1000:
            result = "high volume"
        else:
            result = "low volume"
        print(f"{self.name} detected {result}.")
        return result
