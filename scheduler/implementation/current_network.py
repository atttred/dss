import uuid
from typing import List

from scheduler.abstract.abstract_network import AbstractNetwork
from scheduler.implementation.lai_yang_node import LaiYangNode


class CurrentNetwork(AbstractNetwork):
    def __init__(self):
        self.nodes = []
        self.build_network()
        super().__init__(self.nodes)

    def build_network(self):
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        id3 = uuid.uuid4()

        node1 = LaiYangNode(node_id=id1, neighbors=[id2])
        node2 = LaiYangNode(node_id=id2, neighbors=[id1, id3])
        node3 = LaiYangNode(node_id=id3, neighbors=[id2])

        self.nodes.extend([node1, node2, node3])

    def get_nodes(self):
        return self.nodes


if __name__ == "__main__":
    from scheduler.core.observer import Observer

    network = CurrentNetwork()
    observer = Observer(network)
    observer.run()