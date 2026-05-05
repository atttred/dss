import uuid
from scheduler.abstract.abstract_network import AbstractNetwork
from scheduler.implementation.safra_node import SafraNode
# from scheduler.implementation.rana_node import RanaNode

class CurrentNetwork(AbstractNetwork):
    def __init__(self) -> None:
        self.nodes = []
        
        # Створюємо кільце з 4 вузлів для Сафри
        ids = [uuid.uuid4() for _ in range(4)]
        edges = {
            ids[0]: [ids[1]],  # 0 передає 1
            ids[1]: [ids[2]],  # 1 передає 2
            ids[2]: [ids[3]],  # 2 передає 3
            ids[3]: [ids[0]],  # 3 замикає на 0
        }
        
        for i, node_id in enumerate(ids):
            # Робимо перший вузол (i=0) ініціатором
            node = SafraNode(node_id, edges[node_id])
            node.is_initiator = (i == 0)
            self.nodes.append(node)
            
        super().__init__(self.nodes)