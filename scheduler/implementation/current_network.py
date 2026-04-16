import uuid
from typing import List, Dict
from scheduler.abstract.abstract_network import AbstractNetwork
from scheduler.implementation.election_node import ElectionNode 

class CurrentNetwork(AbstractNetwork):
    def __init__(self) -> None:
        self.nodes = []
        ids = [uuid.uuid4() for _ in range(8)]
        edges = {
            ids[0]: [ids[1], ids[2]],
            ids[1]: [ids[0], ids[3], ids[4]],
            ids[2]: [ids[0], ids[5], ids[6], ids[7]],
            ids[3]: [ids[1]], ids[4]: [ids[1]],
            ids[5]: [ids[2]], ids[6]: [ids[2]], ids[7]: [ids[2]]
        }
        for node_id in ids:
            self.nodes.append(ElectionNode(node_id, edges[node_id]))
        super().__init__(self.nodes)

    def get_nodes(self):
        return self.nodes


if __name__ == "__main__":
    from scheduler.core.observer import Observer

    network = CurrentNetwork()
    observer = Observer(network)
    observer.run()