import uuid
from typing import Union, Any, Dict
from uuid import UUID


class ExternalRequest:
    data: Dict[str, Any]
    transaction_id: uuid.UUID

    def __init__(self, data: Dict[str, Any], transaction_id) -> None:
        self.data = data
        self.transaction_id = transaction_id

    def to_dict(self) -> Dict[str, Union[Dict[str, Any], UUID]]:
        self.data.update({'transaction_id': self.transaction_id})
        return self.data
