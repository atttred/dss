import uuid
from typing import List
from scheduler.implementation.node import Node
from scheduler.core.action import Action
from scheduler.core.node_response import NodeResponse

class ElectionNode(Node):
    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        super().__init__(node_id, neighbors)
        self.candidate = None
        self.parent = None
        self.expected = 0
        self.received = 0

    def process_action(self, message: Action) -> NodeResponse:
        data = message.data
        msg_type = data.get("type") or data.get("message_type")
        c_id = data.get("candidate_id")
        sender = data.get("sender_id")
        outbox = []

        if msg_type == "New":
            if self.candidate is None or str(self.node_id) > str(self.candidate):
                self._start_election(message.action_id, outbox)

        elif msg_type == "EXPLORE":
            if self.candidate is None or str(c_id) > str(self.candidate):
                self.candidate = str(c_id)
                self.parent = sender
                self.received = 0
                self.expected = len(self.neighbors) - 1
                
                for n in self.neighbors:
                    if n != self.parent:
                        outbox.append(self._create_msg(n, "EXPLORE", self.candidate, message.action_id))
                
                if self.expected == 0:
                    outbox.append(self._create_msg(self.parent, "ECHO", self.candidate, message.action_id))
            else:
                outbox.append(self._create_msg(sender, "ECHO", c_id, message.action_id))

        elif msg_type == "ECHO" and str(c_id) == str(self.candidate):
            self.received += 1
            if self.received == self.expected:
                if self.parent == self.node_id:
                    print(f"\n[LEADER] >>> Node {self.node_id} WON! <<<\n")
                else:
                    outbox.append(self._create_msg(self.parent, "ECHO", self.candidate, message.action_id))

        return NodeResponse(outbox)

    def _start_election(self, action_id, outbox):
        self.candidate = str(self.node_id)
        self.parent = self.node_id
        self.expected = len(self.neighbors)
        self.received = 0
        for n in self.neighbors:
            outbox.append(self._create_msg(n, "EXPLORE", self.candidate, action_id))

    def _create_msg(self, to_id, msg_type, c_id, action_id):
        a = Action(data={"type": msg_type, "sender_id": self.node_id, "candidate_id": c_id}, 
                   node_id=to_id, action_id=action_id)
        a.action_type = msg_type
        return a