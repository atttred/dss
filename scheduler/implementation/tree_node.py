import uuid
from typing import List, Set

from scheduler.implementation.node import Node
from scheduler.core.action import Action
from scheduler.core.node_response import NodeResponse


class TreeNode(Node):
    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        super().__init__(node_id, neighbors)
        self._received_from: Set[uuid.UUID] = set()
        self._parent_node: uuid.UUID | None = None
        self._has_decided: bool = False

    def process_action(self, message: Action) -> NodeResponse:
        payload = message.data
        msg_type = payload.get("type") or payload.get("message_type")
        sender = payload.get("sender_id")
        
        outbox: List[Action] = []
        
        if msg_type in ("New", "wakeup"):
            self._start_from_leaves(message.action_id, outbox)
        elif msg_type in ("EXPLORE", "token"):
            self._process_wave(sender, message.action_id, outbox)
        elif msg_type == "DECIDE":
            self._propagate_decision(sender, message.action_id, outbox)

        return NodeResponse(outbox)

    def _start_from_leaves(self, action_id: uuid.UUID, outbox: List[Action]) -> None:
        if len(self.neighbors) == 1 and self._parent_node is None:
            self._parent_node = self.neighbors[0]
            print(f"[TREE] Node {self.node_id} (Leaf) starting wave. Routing to Parent {self._parent_node}.")
            outbox.append(self._create_msg(self._parent_node, "EXPLORE", action_id))

    def _process_wave(self, sender: uuid.UUID, action_id: uuid.UUID, outbox: List[Action]) -> None:
        if sender:
            self._received_from.add(sender)
            
        if len(self._received_from) == len(self.neighbors) - 1 and self._parent_node is None:
            for peer in self.neighbors:
                if peer not in self._received_from:
                    self._parent_node = peer
                    break
            print(f"[TREE] Node {self.node_id} routing wave to Parent {self._parent_node}.")
            outbox.append(self._create_msg(self._parent_node, "EXPLORE", action_id))
            
        elif len(self._received_from) == len(self.neighbors):
            if not self._has_decided:
                self._has_decided = True
                print(f"\n[TREE] >>> Node {self.node_id} collected all waves. ALGORITHM DECIDED! <<<\n")
                for peer in self.neighbors:
                    outbox.append(self._create_msg(peer, "DECIDE", action_id))
                    
    def _propagate_decision(self, sender: uuid.UUID, action_id: uuid.UUID, outbox: List[Action]) -> None:
        if not self._has_decided:
            self._has_decided = True
            print(f"[TREE] Node {self.node_id} received DECIDE. Propagating further.")
            for peer in self.neighbors:
                if peer != sender:
                    outbox.append(self._create_msg(peer, "DECIDE", action_id))

    def _create_msg(self, target_id: uuid.UUID, msg_type: str, action_id: uuid.UUID) -> Action:
        new_action = Action(
            data={"type": msg_type, "sender_id": self.node_id},
            node_id=target_id,
            action_id=action_id or uuid.uuid4()
        )
        new_action.action_type = msg_type
        return new_action