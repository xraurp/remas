from pydantic import BaseModel, model_serializer


class GrafanaAlertLabels(BaseModel):
    default: bool = False
    username: str
    node_id: int
    resource_id: int
    template_id: int

    @model_serializer
    def serialize(self):
        result = {
            "default": str(self.default).lower(),
            "username": self.username,
            "node_id": str(self.node_id),
            "resource_id": str(self.resource_id),
            "template_id": str(self.template_id)
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
        if 'temaplate_id' in data:
            data['temaplate_id'] = int(data['temaplate_id'])
        super().__init__(**data)


