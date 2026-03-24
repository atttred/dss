import uuid
from typing import List
from scheduler.abstract.abstract_node import AbstractNode
from scheduler.core.action import Action
from scheduler.core.mailbox import Mailbox
from scheduler.core.node_response import NodeResponse

class CidonNode(AbstractNode):

    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        self.node_id = node_id
        self.mailbox = Mailbox()
        self.neighbors = neighbors
        self.father = None
        self.unvis = set(neighbors)
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
            self.fwd_token(out)

        elif mtype == 'DISCOVER':
            if not self.first_visit:
                self.first_visit = True
                self.father = snd
                if snd in self.unvis:
                    self.unvis.remove(snd)
                
                for q in self.unvis:
                    out.append(self.make_msg(q, 'VISITED'))
                    
                self.fwd_token(out)
            else:
                out.append(self.make_msg(snd, 'RETURN'))

        elif mtype == 'VISITED':
            if snd in self.unvis:
                self.unvis.remove(snd)

        elif mtype == 'RETURN':
            if snd in self.unvis:
                self.unvis.remove(snd)
            self.fwd_token(out)

        return NodeResponse(out)

    def fwd_token(self, out: List[Action]):
        if self.unvis:
            nxt = self.unvis.pop()
            out.append(self.make_msg(nxt, 'DISCOVER'))
        else:
            if self.father != self.node_id:
                out.append(self.make_msg(self.father, 'RETURN'))
            else:
                print(f"Node {self.node_id} FINISHED")

    def make_msg(self, rec: uuid.UUID, mtype: str) -> Action:
        return Action(
            data={'message_type': mtype, 'sender_id': self.node_id},
            node_id=rec,
            action_id=uuid.uuid4()
        )