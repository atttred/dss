import uuid
from typing import List

from scheduler.implementation.node import Node
from scheduler.core.action import Action
from scheduler.core.node_response import NodeResponse


class RanaNode(Node):
    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        super().__init__(node_id, neighbors)
        self.clock = 0                # Логічний годинник
        self.state = "RELEASED"       # Стани: RELEASED, WANTED, HELD
        self.request_clock = 0        # Годинник на момент нашого запиту
        self.replies_received = 0     # Скільки дозволів отримано
        self.deferred_replies = []    # Черга відкладених відповідей іншим вузлам

    def process_action(self, message: Action) -> NodeResponse:
        data = message.data
        msg_type = data.get("type") or data.get("message_type")
        sender_id = data.get("sender_id")
        req_clock = data.get("clock", 0)
        
        outbox: List[Action] = []

        # 1. Вузол хоче зайти в критичну секцію (CS)
        if msg_type == "REQUEST_CS":
            self.state = "WANTED"
            self.clock += 1
            self.request_clock = self.clock
            self.replies_received = 0
            print(f"[RANA] Node {self.node_id} WANTS to enter CS. Broadcasting REQ(Clock: {self.request_clock})")
            
            # Відправляємо запит УСІМ сусідам
            for neighbor in self.neighbors:
                outbox.append(self._create_msg(neighbor, "REQ", self.request_clock, message.action_id))

        # 2. Отримання запиту від іншого вузла
        elif msg_type == "REQ":
            # Синхронізація годинників (правило Лампорта)
            self.clock = max(self.clock, req_clock) + 1
            
            # Вирішуємо, чи відповідати одразу, чи відкласти:
            # - Якщо ми вже В КРИТИЧНІЙ СЕКЦІЇ (HELD) -> відкладаємо
            # - Якщо ми теж ХОЧЕМО (WANTED), але наш запит старіший (менший годинник) -> відкладаємо
            # - При рівних годинниках порівнюємо ID вузлів (перемагає менший ID)
            defer = False
            if self.state == "HELD":
                defer = True
            elif self.state == "WANTED":
                if (self.request_clock < req_clock) or (self.request_clock == req_clock and str(self.node_id) < str(sender_id)):
                    defer = True

            if defer:
                print(f"[RANA] Node {self.node_id} DEFERRING reply to {sender_id}.")
                self.deferred_replies.append(sender_id)
            else:
                print(f"[RANA] Node {self.node_id} SENDING reply to {sender_id}.")
                outbox.append(self._create_msg(sender_id, "REPLY", self.clock, message.action_id))

        # 3. Отримання дозволу (REPLY)
        elif msg_type == "REPLY":
            self.replies_received += 1
            # Якщо всі сусіди дали дозвіл
            if self.replies_received == len(self.neighbors):
                self.state = "HELD"
                print(f"\n[RANA] >>> Node {self.node_id} ENTERED CRITICAL SECTION! <<<\n")

        # 4. Вихід з критичної секції
        elif msg_type == "RELEASE_CS":
            if self.state == "HELD":
                print(f"[RANA] Node {self.node_id} LEAVING Critical Section.")
                self.state = "RELEASED"
                # Відправляємо REPLY усім, кого змусили чекати
                for deferred_node in self.deferred_replies:
                    outbox.append(self._create_msg(deferred_node, "REPLY", self.clock, message.action_id))
                self.deferred_replies.clear()

        return NodeResponse(outbox)

    def _create_msg(self, target_id: uuid.UUID, msg_type: str, current_clock: int, action_id: uuid.UUID) -> Action:
        a = Action(
            data={"type": msg_type, "sender_id": self.node_id, "clock": current_clock},
            node_id=target_id,
            action_id=action_id or uuid.uuid4()
        )
        a.action_type = msg_type
        return a