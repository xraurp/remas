from string import Template
from src.db.models import (
    Node
)
import httpx
import json
from fastapi import HTTPException
from src.app_logic.grafana_general_operations import (
    upload_grafana_config,
    get_folders_from_grafana
)

# TODO - use this as node template
json.dumps({
    "dashboard": {
        "id": None,
        "uid": None,
        "title": "Node ${node_name} overview",
        "tags": [ "${node_name}", "${node_id}" ],
        "timezone": "browser",
        "schemaVersion": 16,
        "refresh": "30s"
    },
    "folderUid": "",
    "message": "",
    "overwrite": True
})


# TODO - remove node dashboard
# TODO - update node dashboard
# TODO - get node dashboard

# TODO - fix this fucntion
def grafana_add_node_dashboard(node: Node) -> None:
    """
    Creates dashboard for given node in Grafana.
    :param node (Node): node to add dashboard for
    """
    template = Template(node.dashboard_template.template)
    dashboard_folder = get_folders_from_grafana(
        folder_names=['node_dashboards']
    )[0]

    dashboard_config = template.safe_substitute(
        node_id=node.id,
        node_name=node.name,
        node_description=node.description
    )
    dashboard_config = json.loads(dashboard_config)
    dashboard_config['folderUid'] = dashboard_folder['uid']
    dashboard_config['message'] = 'Created node dashboard on node init.'

    # Upload config to grafana
    try:
        upload_grafana_config(
            config=dashboard_config,
            path='/api/v1/provisioning/alert-rules'
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to create dashboard for node in Grafana!"
        )
