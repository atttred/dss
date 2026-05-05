import uuid
from typing import List

from scheduler.implementation.node import Node
from scheduler.core.action import Action
from scheduler.core.node_response import NodeResponse


class MerlinSegallNode(Node):
    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        super().__init__(node_id, neighbors)
        self.distance = float('inf')  # Найкоротша відома відстань до стоку (початково нескінченність)
        self.parent = None            # Вузол, через який пролягає найкоротший шлях
        self.is_sink = False          # Чи є цей вузол стоком (ціллю)

    def process_action(self, message: Action) -> NodeResponse:
        data = message.data
        msg_type = data.get("type") or data.get("message_type")
        sender = data.get("sender_id")
        sender_dist = data.get("dist", float('inf'))
        
        outbox: List[Action] = []

        # 1. Ініціалізація стоку (Sink). Стік запускає побудову дерева.
        if msg_type == "START_SINK":
            if not self.is_sink:
                self.is_sink = True
                self.distance = 0
                self.parent = self.node_id
                print(f"[MERLIN-SEGALL] Node {self.node_id} is SINK. Broadcasting distance 0.")
                
                # Стік повідомляє всім сусідам свою відстань (0)
                for neighbor in self.neighbors:
                    outbox.append(self._create_msg(neighbor, "UPDATE", self.distance, message.action_id))

        # 2. Отримання оновлення відстані від сусіда
        elif msg_type == "UPDATE":
            # Розраховуємо нову відстань через цього сусіда (вага ребра = 1)
            new_distance = sender_dist + 1
            
            # Якщо знайдено коротший шлях до стоку
            if new_distance < self.distance:
                print(f"[MERLIN-SEGALL] Node {self.node_id} found shorter path: {new_distance} via {sender}.")
                self.distance = new_distance
                self.parent = sender
                
                # Розсилаємо СВОЮ нову найкоротшу відстань усім сусідам
                for neighbor in self.neighbors:
                    # Опціонально: можна не відправляти назад батьку (Split Horizon),
                    # але класичний алгоритм розсилає всім.
                    outbox.append(self._create_msg(neighbor, "UPDATE", self.distance, message.action_id))

        return NodeResponse(outbox)

    def _create_msg(self, target_id: uuid.UUID, msg_type: str, dist: int, action_id: uuid.UUID) -> Action:
        """Створює об'єкт Action з динамічним додаванням атрибуту, обходячи обмеження core."""
        new_action = Action(
            data={"type": msg_type, "sender_id": self.node_id, "dist": dist},
            node_id=target_id,
            action_id=action_id or uuid.uuid4()
        )
        new_action.action_type = msg_type
        return new_action