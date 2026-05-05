import uuid
from typing import List

from scheduler.implementation.node import Node
from scheduler.core.action import Action
from scheduler.core.node_response import NodeResponse


class SafraNode(Node):
    def __init__(self, node_id: uuid.UUID, neighbors: List[uuid.UUID]):
        super().__init__(node_id, neighbors)
        self.color = "white"        # Спочатку вузол білий
        self.msg_count = 0          # Баланс повідомлень: +1 при відправці, -1 при отриманні
        self.is_active = False      # Стан вузла (працює чи ні)
        self.is_initiator = False   # Чи є цей вузол ініціатором (вузол 0)

    def process_action(self, message: Action) -> NodeResponse:
        data = message.data
        msg_type = data.get("type") or data.get("message_type")
        sender = data.get("sender_id")
        
        outbox: List[Action] = []

        # 1. Симуляція роботи: Вузол починає працювати (стає активним)
        if msg_type == "START_WORK":
            self.is_active = True
            self.is_initiator = data.get("is_initiator", False)
            print(f"[SAFRA] Node {self.node_id} is ACTIVE.")

        # 2. Відправка звичайного повідомлення іншому вузлу
        elif msg_type == "SEND_BASIC":
            target = data.get("target_id")
            self.msg_count += 1  # Фіксуємо відправку
            outbox.append(self._create_msg(target, "BASIC", message.action_id))
            print(f"[SAFRA] Node {self.node_id} sent BASIC msg. Count: {self.msg_count}")

        # 3. Отримання звичайного повідомлення
        elif msg_type == "BASIC":
            self.msg_count -= 1  # Фіксуємо отримання
            self.color = "black" # Правило Сафри: отримав повідомлення -> став чорним
            self.is_active = True
            print(f"[SAFRA] Node {self.node_id} received BASIC msg. Color -> BLACK. Count: {self.msg_count}")

        # 4. Ініціація алгоритму виявлення завершення (запускає тільки ініціатор)
        elif msg_type == "INIT_TOKEN" and self.is_initiator:
            print(f"\n[SAFRA] Initiator {self.node_id} starts TOKEN circulation.\n")
            # Ініціатор випускає білий маркер з лічильником 0
            next_node = self.neighbors[0] # В кільці завжди є наступний сусід
            outbox.append(self._create_token_msg(next_node, "white", 0, message.action_id))

        # 5. Отримання і обробка маркера (TOKEN)
        elif msg_type == "TOKEN":
            token_color = data.get("token_color")
            token_count = data.get("token_count", 0)

            # Алгоритм вимагає, щоб вузол передав маркер лише тоді, коли він ПАСИВНИЙ
            # (Для симуляції припустимо, що ми стаємо пасивними одразу після отримання токена, якщо не обробляємо нічого іншого)
            self.is_active = False

            # Якщо маркер повернувся до ініціатора
            if self.is_initiator:
                if self.color == "white" and token_color == "white" and (token_count + self.msg_count) == 0:
                    print(f"\n[SAFRA] >>> TERMINATION DETECTED by {self.node_id}! System is idle. <<<\n")
                else:
                    print(f"[SAFRA] Initiator {self.node_id} sees system is NOT terminated. Restarting TOKEN.")
                    self.color = "white"
                    next_node = self.neighbors[0]
                    outbox.append(self._create_token_msg(next_node, "white", 0, message.action_id))
            
            # Якщо це звичайний вузол у кільці
            else:
                new_token_count = token_count + self.msg_count
                new_token_color = "black" if self.color == "black" or token_color == "black" else "white"
                
                print(f"[SAFRA] Node {self.node_id} passing TOKEN. Token Color: {new_token_color}, Count: {new_token_count}")
                self.color = "white" # Після передачі маркера вузол знову стає білим
                
                next_node = self.neighbors[0]
                outbox.append(self._create_token_msg(next_node, new_token_color, new_token_count, message.action_id))

        return NodeResponse(outbox)

    def _create_msg(self, target_id: uuid.UUID, msg_type: str, action_id: uuid.UUID) -> Action:
        a = Action(data={"type": msg_type, "sender_id": self.node_id}, node_id=target_id, action_id=action_id or uuid.uuid4())
        a.action_type = msg_type
        return a

    def _create_token_msg(self, target_id: uuid.UUID, color: str, count: int, action_id: uuid.UUID) -> Action:
        a = Action(
            data={"type": "TOKEN", "sender_id": self.node_id, "token_color": color, "token_count": count},
            node_id=target_id,
            action_id=action_id or uuid.uuid4()
        )
        a.action_type = "TOKEN"
        return a