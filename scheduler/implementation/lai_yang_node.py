import uuid
from typing import List

from scheduler.implementation.node import Node
from scheduler.core.action import Action
from scheduler.core.node_response import NodeResponse


class LaiYangNode(Node):
    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        super().__init__(node_id, neighbors)
        self.color = "white" 
        self.snapshot_taken = False
        self.in_transit_messages = [] 

    def process_action(self, message: Action) -> NodeResponse:
        payload = message.data
        msg_type = payload.get("type") or payload.get("message_type")
        
        msg_color = payload.get("color", "white") 
        sender = payload.get("sender_id")
        
        outbox: List[Action] = []

        if self.color == "white" and msg_color == "red":
            print(f"[LAI-YANG] Node {self.node_id} forced RED by a RED message from {sender}.")
            self._take_snapshot(outbox, message.action_id)

        if self.color == "red" and msg_color == "white" and sender is not None:
            print(f"[LAI-YANG] Node {self.node_id} (RED) caught WHITE in-transit message from {sender}.")
            self.in_transit_messages.append({"from": sender, "type": msg_type})

        if msg_type in ("New", "INIT_SNAPSHOT"):
            if self.color == "white":
                print(f"[LAI-YANG] Node {self.node_id} initiated snapshot externally.")
                self._take_snapshot(outbox, message.action_id)

        elif msg_type == "COMPUTATION":
            pass 

        return NodeResponse(outbox)

    def _take_snapshot(self, outbox: List[Action], action_id: uuid.UUID) -> None:
        self.color = "red"
        self.snapshot_taken = True
        print(f"   -> Node {self.node_id} recorded its local state.")
        
        for peer in self.neighbors:
            outbox.append(self._create_msg(peer, "COMPUTATION", action_id))

    def _create_msg(self, target_id: uuid.UUID, msg_type: str, action_id: uuid.UUID) -> Action:
        new_action = Action(
            data={"type": msg_type, "sender_id": self.node_id, "color": self.color},
            node_id=target_id,
            action_id=action_id or uuid.uuid4()
        )
        new_action.action_type = msg_type
        return new_action