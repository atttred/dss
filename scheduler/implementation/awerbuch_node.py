import uuid
from typing import List
from scheduler.abstract.abstract_node import AbstractNode
from scheduler.core.action import Action
from scheduler.core.mailbox import Mailbox
from scheduler.core.node_response import NodeResponse

class AwerbuchNode(AbstractNode):

    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        self.node_id = node_id
        self.mailbox = Mailbox()
        self.neighbors = neighbors
        self.father = None
        self.unvis = set(neighbors)
        self.flags = {n: 0 for n in neighbors}
        self.first_visit = False

    def process_action(self, msg: Action) -> NodeResponse:
        mtype = msg.data.get('message_type')
        snd = msg.data.get('sender_id')
        out = []

        print(f"Node {self.node_id} processing {mtype} from {snd}")

        if mtype == 'New':
            self.first_visit = True
            self.father = self.node_id
            for q in self.neighbors:
                out.append(self.make_msg(q, 'VISITED'))
                self.flags[q] = 1
                
            if not self.neighbors:
                print(f"Node {self.node_id} FINISHED")
            elif all(v == 0 for v in self.flags.values()):
                out.append(self.make_msg(self.node_id, 'RETURN_SELF'))

        elif mtype == 'DISCOVER':
            if not self.first_visit:
                self.first_visit = True
                self.father = snd
                
                for q in self.neighbors:
                    if q != snd:
                        out.append(self.make_msg(q, 'VISITED'))
                        self.flags[q] = 1
                
                if len(self.neighbors) == 1 and self.neighbors[0] == snd:
                    out.append(self.make_msg(snd, 'RETURN'))
                elif all(v == 0 for v in self.flags.values()):
                    out.append(self.make_msg(self.node_id, 'RETURN_SELF'))

        elif mtype == 'VISITED':
            if snd in self.unvis:
                self.unvis.remove(snd)
            out.append(self.make_msg(snd, 'ACK'))

        elif mtype == 'ACK':
            self.flags[snd] = 0
            if all(v == 0 for v in self.flags.values()):
                out.append(self.make_msg(self.node_id, 'RETURN_SELF'))

        elif mtype in ('RETURN', 'RETURN_SELF'):
            if self.unvis:
                k = self.unvis.pop()
                out.append(self.make_msg(k, 'DISCOVER'))
            else:
                if self.father != self.node_id:
                    out.append(self.make_msg(self.father, 'RETURN'))
                else:
                    print(f"Node {self.node_id} FINISHED")

        return NodeResponse(out)

    def make_msg(self, rec: uuid.UUID, mtype: str) -> Action:
        return Action(
            data={'message_type': mtype, 'sender_id': self.node_id},
            node_id=rec,
            action_id=uuid.uuid4()
        )