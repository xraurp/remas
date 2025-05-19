import httpx
from src.config import get_settings
from fastapi import HTTPException

def join_url_path(*args) -> str:
    """
    Joins parts of URL path together.
    :param args: parts of the URL paths to join
    :return (str): joined URL path
    """
    return '/'.join(map(lambda x: str(x).strip('/'), args))

def upload_grafana_config(
    config: dict,
    path: str,
    method: str = 'POST'
) -> httpx.Response:
    """
    Uploads configuration to grafana instance.
    :param config (dict): configuration to upload (json)
    :Param path (str): location on the instance where to upload the config
        -> (https://grafana.instance/{path}) <-
    :param method (str): HTTP method (POST, GET, etc.) (default: POST)
    :return (httpx.Response): response
    """
    response = httpx.request(
        method=method,
        url=join_url_path(get_settings().grafana_url, path),
        auth=(get_settings().grafana_username, get_settings().grafana_password),
        json=config
    )
    # Raise error with response message if error has occured
    response.raise_for_status()
    return response

def remove_grafana_config(path: str) -> None:
    """
    Removes configured entity (like alert rule, dashboard, etc.) from Grafana.
    :param path (str): path to given entity
    """
    response = httpx.request(
        method='DELETE',
        url=join_url_path(get_settings().grafana_url, path),
        auth=(get_settings().grafana_username, get_settings().grafana_password)
    )
    response.raise_for_status()

def get_grafana_config(path: str) -> httpx.Response:
    """
    Gets config from given API path from Grafana.
    :param path (str): path on Grafana instance API
    :return (httpx.Response): response
    """
    response = httpx.request(
        method='GET',
        url=join_url_path(get_settings().grafana_url, path),
        auth=(get_settings().grafana_username, get_settings().grafana_password),
    )
    # Raise error with response message if error has occured
    response.raise_for_status()
    return response

def get_folders_from_grafana(folder_names: list[str]) -> list[dict]:
    """
    Gets folders with given names from Grafana.
    :param folder_names (list[str]): list of folder names
    :return (list[dict]): folders from Grafana
    """
    try:
        folders = get_grafana_config('/api/folders').json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get folder list from Grafana!"
        )
    
    return list(filter(
        lambda f: f.get('title', '') in folder_names,
        folders
    ))
