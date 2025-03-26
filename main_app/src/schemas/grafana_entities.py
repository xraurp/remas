from pydantic import BaseModel, model_serializer


class GrafanaAlertLabels(BaseModel):
    default: bool = False
    username: str
    notification_owner: str
    node_id: int
    resource_id: int
    notification_id: int

    @model_serializer
    def serialize(self):
        result = {
            "default": str(self.default).lower(),
            "username": self.username,
            "notification_owner": self.notification_owner,
            "node_id": str(self.node_id),
            "resource_id": str(self.resource_id),
            "notification_id": str(self.notification_id)
        }
        return result

    def __init__(self, **data):
        if 'default' in data:
            if data['default'] == 'true':
                data['default'] = True
            elif data['default'] == 'false':
                data['default'] = False
        if 'node_id' in data:
            data['node_id'] = int(data['node_id'])
        if 'resource_id' in data:
            data['resource_id'] = int(data['resource_id'])
        if 'notification_id' in data:
            data['notification_id'] = int(data['notification_id'])
        super().__init__(**data)


