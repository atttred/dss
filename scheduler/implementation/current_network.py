import uuid
from scheduler.abstract.abstract_network import AbstractNetwork
from scheduler.implementation.merlin_segall_node import MerlinSegallNode

class CurrentNetwork(AbstractNetwork):
    def __init__(self) -> None:
        self.nodes = []
        
        # Створюємо 5 вузлів
        ids = [uuid.uuid4() for _ in range(5)]
        
        # Топологія:
        # 0 -- 1 -- 2
        # |         |
        # 3 -- 4 ----
        # Шлях від 2 до 0 через 1 дорівнює 2 крокам.
        # Шлях від 2 до 0 через 4 і 3 дорівнює 3 крокам.
        edges = {
            ids[0]: [ids[1], ids[3]],
            ids[1]: [ids[0], ids[2]],
            ids[2]: [ids[1], ids[4]],
            ids[3]: [ids[0], ids[4]],
            ids[4]: [ids[3], ids[2]],
        }
        
        for node_id in ids:
            self.nodes.append(MerlinSegallNode(node_id, edges[node_id]))
            
        super().__init__(self.nodes)