#!/usr/bin/env python3
import httpx
import json

def login(username: str, password: str):
    """
    Login to Grafana.
    """
    response = httpx.post(
        url='http://localhost:8000/authentication/token',
        data={'username': username, 'password': password}
    )
    return response.json()['access_token']

def uplaod_CPU_notification(token: str) -> None:
    cpu_treshold_template = open(
        "../grafana_templates/CPU_Notificaion_template.json",
        "r"
    )
    cpu_notification = httpx.post(
        url='http://localhost:8000/notification',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'Default user CPU threshold',
            'type': 'grafana_resource_exceedance_task',
            'description': 'User exceeded CPU limit!',
            'notification_template': cpu_treshold_template.read(),
            'resource_id': 40,
            'default_amount': 1
        }
    )
    cpu_notification.raise_for_status()
    cpu_notification = cpu_notification.json()
    cpu_treshold_template.close()
    print(json.dumps(cpu_notification, indent=4))

def uplaod_memory_notification(token: str) -> None:
    memory_treshold_template = open(
        "../grafana_templates/Memory_Notification_template.json",
        "r"
    )
    memory_notification = httpx.post(
        url='http://localhost:8000/notification',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'Default user memory threshold',
            'type': 'grafana_resource_exceedance_task',
            'description': 'User memory exceeded limit!',
            'notification_template': memory_treshold_template.read(),
            'default_amount': 400 * 1024 * 1024,
            'resource_id': 39
        }
    )
    memory_notification.raise_for_status()
    memory_notification = memory_notification.json()
    memory_treshold_template.close()
    print(json.dumps(memory_notification, indent=4))

def main() -> None:
    token = login('admin', 'admin')
    uplaod_CPU_notification(token)
    uplaod_memory_notification(token)

if __name__ == '__main__':
    main()
