import uuid
from typing import List

from scheduler.implementation.node import Node
from scheduler.core.action import Action
from scheduler.core.node_response import NodeResponse


class EchoNode(Node):
    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        super().__init__(node_id, neighbors)
        self._parent_node: uuid.UUID | None = None
        self._messages_processed: int = 0
        self._is_root_initiator: bool = False

    def process_action(self, message: Action) -> NodeResponse:
        payload = message.data
        wave_type = payload.get("type") or payload.get("message_type")
        sender = payload.get("sender_id")
        
        outgoing_actions: List[Action] = []

        if wave_type in ("New", "init"):
            self._handle_initial_wakeup(message.action_id, outgoing_actions)
        elif wave_type in ("EXPLORE", "ECHO"):
            self._handle_incoming_wave(wave_type, sender, message.action_id, outgoing_actions)

        return NodeResponse(outgoing_actions)

    def _handle_initial_wakeup(self, action_id: uuid.UUID, outbox: List[Action]) -> None:
        if self._is_root_initiator or self._parent_node is not None:
            return
            
        self._is_root_initiator = True
        print(f"[ECHO] Node {self.node_id} acts as INITIATOR. Broadcasting EXPLORE.")
        
        for peer in self.neighbors:
            outbox.append(self._generate_reply(peer, "EXPLORE", action_id))

    def _handle_incoming_wave(self, wave_type: str, sender: uuid.UUID, action_id: uuid.UUID, outbox: List[Action]) -> None:
        if wave_type == "EXPLORE" and self._parent_node is None and not self._is_root_initiator:
            self._parent_node = sender
            print(f"[ECHO] Node {self.node_id} designates {sender} as its Parent.")
            
            for peer in self.neighbors:
                if peer != self._parent_node:
                    outbox.append(self._generate_reply(peer, "EXPLORE", action_id))

        self._messages_processed += 1

        if self._messages_processed == len(self.neighbors):
            if self._is_root_initiator:
                print(f"\n[ECHO] >>> Node {self.node_id} (Initiator) collected all acks. ALGORITHM DECIDED! <<<\n")
            else:
                print(f"[ECHO] Node {self.node_id} completed its wait. Returning ECHO to Parent {self._parent_node}.")
                outbox.append(self._generate_reply(self._parent_node, "ECHO", action_id))

    def _generate_reply(self, target_id: uuid.UUID, msg_type: str, action_id: uuid.UUID) -> Action:
        new_action = Action(
            data={"type": msg_type, "sender_id": self.node_id},
            node_id=target_id,
            action_id=action_id or uuid.uuid4()
        )
        new_action.action_type = msg_type
        return new_action