#!/usr/bin/env python3

import httpx
import json

# Grafana integration tests

def login(username: str, password: str):
    """
    Login to Grafana.
    """
    response = httpx.post(
        url='http://localhost:8000/authentication/token',
        data={'username': username, 'password': password}
    )
    return response.json()['access_token']


def main():
    token = login('administrator', 'admin')

    # Add user
    print('Adding user.')
    input("Press Enter to continue...")
    user1 = httpx.post(
        url='http://localhost:8000/user',
        headers={
            'Authorization': f'Bearer {token}'
        },
        json={
            'name': 'User1',
            'surname': 'User1',
            'email': 'user1@localhost',
            'username': 'user1',
            'password': 'user1',
            'uid': 1000
        }
    )
    user1.raise_for_status()
    user1 = user1.json()
    print(json.dumps(user1, indent=4))

    # Add localhost
    print('Adding localhost node.')
    input("Press Enter to continue...")
    localhost_node = httpx.post(
        url='http://localhost:8000/node',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'localhost',
            'description': 'localhost test node'
        }
    )
    localhost_node.raise_for_status()
    localhost_node = localhost_node.json()
    print(json.dumps(localhost_node, indent=4))

    # Add vm_node
    print('Adding vm node.')
    input("Press Enter to continue...")
    vm_node = httpx.post(
        url='http://localhost:8000/node',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': '192.168.122.84',
            'description': 'Test VM node'
        }
    )
    vm_node.raise_for_status()
    vm_node = vm_node.json()

    print(json.dumps(vm_node, indent=4))

    # Add resource CPU
    print('Adding CPU resource.')
    input("Press Enter to continue...")
    cpu_resource = httpx.post(
        url='http://localhost:8000/resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'CPU',
            'description': 'CPU resource'
        }
    )
    cpu_resource.raise_for_status()
    cpu_resource = cpu_resource.json()
    print(json.dumps(cpu_resource, indent=4))

    # Add resource memory
    print('Adding memory resource.')
    input("Press Enter to continue...")
    memory_resource = httpx.post(
        url='http://localhost:8000/resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'memory',
            'description': 'memory resource'
        }
    )
    memory_resource.raise_for_status()
    memory_resource = memory_resource.json()
    print(json.dumps(memory_resource, indent=4))

    # Assign CPU to localhost
    print('Assigning CPU to localhost.')
    input("Press Enter to continue...")
    cpu_to_localhost = httpx.post(
        url='http://localhost:8000/node/add_resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'node_id': localhost_node['id'],
            'resource_id': cpu_resource['id'],
            'amount': 16
        }
    )
    cpu_to_localhost.raise_for_status()
    cpu_to_localhost = cpu_to_localhost.json()
    print(json.dumps(cpu_to_localhost, indent=4))


    # Create Notification for CPU
    print('Adding CPU notification template.')
    input("Press Enter to continue...")
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
            'default_amount': 1,
            'resource_id': cpu_resource['id']
        }
    )
    cpu_notification.raise_for_status()
    cpu_notification = cpu_notification.json()
    cpu_treshold_template.close()
    print(json.dumps(cpu_notification, indent=4))


    # Assign CPU Notification to All group
    print('Assigning CPU Notification to All group.')
    input("Press Enter to continue...")
    cpu_notification_to_all = httpx.post(
        url='http://localhost:8000/notification/assign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': 1,
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_to_all.raise_for_status()
    cpu_notification_to_all = cpu_notification_to_all.json()
    print(json.dumps(cpu_notification_to_all, indent=4))


    # Create wrong Notification for memory
    print('Adding memory notification template.')
    input("Press Enter to continue...")
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
            'default_amount': 1,
            'resource_id': memory_resource['id']
        }
    )
    memory_notification.raise_for_status()
    memory_notification = memory_notification.json()
    memory_treshold_template.close()
    print(json.dumps(memory_notification, indent=4))


    # Assign Memory Notification to All group
    print('Assigning Memory Notification to All group.')
    input("Press Enter to continue...")
    memory_notification_to_all = httpx.post(
        url='http://localhost:8000/notification/assign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': 1,
            'notification_id': memory_notification['id']
        }
    )
    memory_notification_to_all.raise_for_status()
    memory_notification_to_all = memory_notification_to_all.json()
    print(json.dumps(memory_notification_to_all, indent=4))


    # Assign memory to localhost
    print('Assigning memory to localhost.')
    input("Press Enter to continue...")
    memory_to_localhost = httpx.post(
        url='http://localhost:8000/node/add_resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'node_id': localhost_node['id'],
            'resource_id': memory_resource['id'],
            'amount': 16 * (1024 ** 3)
        }
    )
    memory_to_localhost.raise_for_status()
    memory_to_localhost = memory_to_localhost.json()
    print(json.dumps(memory_to_localhost, indent=4))


    # Update Notification for memory
    print('Adding memory corect notification template.')
    input("Press Enter to continue...")
    memory_treshold_template = open(
        "../grafana_templates/Memory_Notification_template.json",
        "r"
    )
    memory_notification = httpx.put(
        url='http://localhost:8000/notification',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'id': memory_notification['id'],
            'name': 'Default user memory threshold',
            'type': 'grafana_resource_exceedance_task',
            'description': 'User memory exceeded limit!',
            'notification_template': memory_treshold_template.read(),
            'default_amount': 400 * 1024 * 1024,
            'resource_id': memory_resource['id']
        }
    )
    memory_notification.raise_for_status()
    memory_notification = memory_notification.json()
    memory_treshold_template.close()
    print(json.dumps(memory_notification, indent=4))


    # Remove CPU from localhost
    print('Removing CPU from localhost.')
    input("Press Enter to continue...")
    cpu_from_localhost = httpx.post(
        url=f'http://localhost:8000/node/remove_resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'node_id': localhost_node['id'],
            'resource_id': cpu_resource['id'],
            'amount': 0
        }
    )
    cpu_from_localhost.raise_for_status()
    cpu_from_localhost = cpu_from_localhost.json()
    print(json.dumps(cpu_from_localhost, indent=4))


    # Assign CPU to vm_node
    print('Adding CPU resource to vm node.')
    input("Press Enter to continue...")
    cpu_to_vm_node = httpx.post(
        url='http://localhost:8000/node/add_resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'node_id': vm_node['id'],
            'resource_id': cpu_resource['id'],
            'amount': 4
        }
    )
    cpu_to_vm_node.raise_for_status()
    cpu_to_vm_node = cpu_to_vm_node.json()
    print(json.dumps(cpu_to_vm_node, indent=4))


    # Remove CPU Notification from All group
    print('Removing CPU Notification from All group.')
    input("Press Enter to continue...")
    cpu_notification_from_all = httpx.post(
        url=f'http://localhost:8000/notification/unassign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': 1,
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_from_all.raise_for_status()
    cpu_notification_from_all = cpu_notification_from_all.json()
    print(json.dumps(cpu_notification_from_all, indent=4))


    # Assign CPU Notification to user1
    print('Assigning CPU Notification to user1.')
    input("Press Enter to continue...")
    cpu_notification_to_user1 = httpx.post(
        url='http://localhost:8000/notification/assign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'user_id': user1['id'],
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_to_user1.raise_for_status()
    cpu_notification_to_user1 = cpu_notification_to_user1.json()
    print(json.dumps(cpu_notification_to_user1, indent=4))


    # Remove CPU from vm_node
    print('Removing CPU from vm node.')
    input("Press Enter to continue...")
    cpu_from_vm_node = httpx.post(
        url=f'http://localhost:8000/node/remove_resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'node_id': vm_node['id'],
            'resource_id': cpu_resource['id'],
            'amount': 0
        }
    )
    cpu_from_vm_node.raise_for_status()
    cpu_from_vm_node = cpu_from_vm_node.json()
    print(json.dumps(cpu_from_vm_node, indent=4))


    # Remove CPU Notification from user1
    print('Removing CPU Notification from user1.')
    input("Press Enter to continue...")
    cpu_notification_from_user1 = httpx.post(
        url=f'http://localhost:8000/notification/unassign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'user_id': user1['id'],
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_from_user1.raise_for_status()
    cpu_notification_from_user1 = cpu_notification_from_user1.json()
    print(json.dumps(cpu_notification_from_user1, indent=4))


    # Assign CPU Notification to All group
    print('Assigning CPU Notification to All group.')
    input("Press Enter to continue...")
    cpu_notification_to_all = httpx.post(
        url='http://localhost:8000/notification/assign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': 1,
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_to_all.raise_for_status()
    cpu_notification_to_all = cpu_notification_to_all.json()
    print(json.dumps(cpu_notification_to_all, indent=4))


    # Add user
    print('Adding test user.')
    input("Press Enter to continue...")
    test_user = httpx.post(
        url='http://localhost:8000/user',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'test',
            'email': 'test@localhost',
            'password': 'test',
            'name': 'Test',
            'surname': 'Test',
            'uid': 1001
        }
    )
    test_user.raise_for_status()
    test_user = test_user.json()
    print(json.dumps(test_user, indent=4))


    # Assign CPU to vm_node
    print('Assigning CPU to vm node.')
    input("Press Enter to continue...")
    cpu_to_vm_node = httpx.post(
        url='http://localhost:8000/node/add_resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'node_id': vm_node['id'],
            'resource_id': cpu_resource['id'],
            'amount': 4
        }
    )
    cpu_to_vm_node.raise_for_status()
    cpu_to_vm_node = cpu_to_vm_node.json()
    print(json.dumps(cpu_to_vm_node, indent=4))


    # Create Subgroup for user
    print('Creating user subgroup.')
    input("Press Enter to continue...")
    subgroup = httpx.post(
        url='http://localhost:8000/group',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'Users Subgroup',
            'parent_id': 3
        }
    )
    subgroup.raise_for_status()
    subgroup = subgroup.json()
    print(json.dumps(subgroup, indent=4))


    # Assign CPU Notification to subgroup
    print('Assigning CPU Notification to subgroup.')
    input("Press Enter to continue...")
    cpu_notification_to_subgroup = httpx.post(
        url='http://localhost:8000/notification/assign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': subgroup['id'],
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_to_subgroup.raise_for_status()
    cpu_notification_to_subgroup = cpu_notification_to_subgroup.json()
    print(json.dumps(cpu_notification_to_subgroup, indent=4))


    # Remove CPU Notification from All group
    print('Removing CPU Notification from All group.')
    input("Press Enter to continue...")
    cpu_notification_from_all = httpx.post(
        url=f'http://localhost:8000/notification/unassign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': 1,
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_from_all.raise_for_status()
    cpu_notification_from_all = cpu_notification_from_all.json()
    print(json.dumps(cpu_notification_from_all, indent=4))


    # Move user1 to subgroup
    print('Moving user1 to subgroup.')
    input("Press Enter to continue...")
    user1_to_subgroup = httpx.post(
        url='http://localhost:8000/group/add_user',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': subgroup['id'],
            'user_id': user1['id']
        }
    )
    user1_to_subgroup.raise_for_status()
    user1_to_subgroup = user1_to_subgroup.json()
    print(json.dumps(user1_to_subgroup, indent=4))


    # Remove Subgroup
    print('Removing Subgroup.')
    input("Press Enter to continue...")
    subgroup_rm = httpx.delete(
        url=f'http://localhost:8000/group/{subgroup["id"]}',
        headers={'Authorization': f'Bearer {token}'}
    )
    subgroup_rm.raise_for_status()
    subgroup_rm = subgroup_rm.json()
    print(json.dumps(subgroup_rm, indent=4))


    # Reasign CPU Notification to All group
    print('Assigning CPU Notification to All group.')
    input("Press Enter to continue...")
    cpu_notification_to_all = httpx.post(
        url='http://localhost:8000/notification/assign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': 1,
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_to_all.raise_for_status()
    cpu_notification_to_all = cpu_notification_to_all.json()
    print(json.dumps(cpu_notification_to_all, indent=4))


    # Remove user
    print('Removing test user.')
    input("Press Enter to continue...")
    test_user_rm = httpx.delete(
        url=f'http://localhost:8000/user/{test_user["id"]}',
        headers={'Authorization': f'Bearer {token}'}
    )
    test_user_rm.raise_for_status()
    test_user_rm = test_user_rm.json()
    print(json.dumps(test_user_rm, indent=4))


    # Remove localhost
    print('Removing localhost node.')
    input("Press Enter to continue...")
    node1_rm = httpx.delete(
        url=f'http://localhost:8000/node/{localhost_node["id"]}',
        headers={'Authorization': f'Bearer {token}'}
    )
    node1_rm.raise_for_status()
    node1_rm = node1_rm.json()
    print(json.dumps(node1_rm, indent=4))


    # Remove CPU Notification
    print('Removing CPU Notification.')
    input("Press Enter to continue...")
    cpu_notification_rm = httpx.delete(
        url=f'http://localhost:8000/notification/{cpu_notification["id"]}',
        headers={'Authorization': f'Bearer {token}'}
    )
    cpu_notification_rm.raise_for_status()
    cpu_notification_rm = cpu_notification_rm.json()
    print(json.dumps(cpu_notification_rm, indent=4))


    # Assign memory to vm node
    print('Assigning memory to localhost.')
    input("Press Enter to continue...")
    memory_to_localhost = httpx.post(
        url='http://localhost:8000/node/add_resource',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'node_id': vm_node['id'],
            'resource_id': memory_resource['id'],
            'amount': 4 * (1024 ** 3)
        }
    )
    memory_to_localhost.raise_for_status()
    memory_to_localhost = memory_to_localhost.json()
    print(json.dumps(memory_to_localhost, indent=4))


    # Remove Memory Resource
    print('Removing Memory Resource.')
    input("Press Enter to continue...")
    memory_resource_rm = httpx.delete(
        url=f'http://localhost:8000/resource/{memory_resource["id"]}',
        headers={'Authorization': f'Bearer {token}'}
    )
    memory_resource_rm.raise_for_status()
    memory_resource_rm = memory_resource_rm.json()
    print(json.dumps(memory_resource_rm, indent=4))


    # Add Notification for CPU again
    print('Adding Notification for CPU again.')
    input("Press Enter to continue...")
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
            'resource_id': cpu_resource['id'],
            'default_amount': 1
        }
    )
    cpu_notification.raise_for_status()
    cpu_notification = cpu_notification.json()
    cpu_treshold_template.close()
    print(json.dumps(cpu_notification, indent=4))


    # Assign CPU Notification to All group
    print('Assigning CPU Notification to All group.')
    input("Press Enter to continue...")
    cpu_notification_to_all = httpx.post(
        url='http://localhost:8000/notification/assign',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'group_id': 1,
            'notification_id': cpu_notification['id']
        }
    )
    cpu_notification_to_all.raise_for_status()
    cpu_notification_to_all = cpu_notification_to_all.json()
    print(json.dumps(cpu_notification_to_all, indent=4))


    # Assign CPU Notification to CPU resource
    print('Assigning CPU Notification to CPU resource.')
    input("Press Enter to continue...")
    cpu_notification_assign = cpu_notification_to_all.copy()
    cpu_notification_assign['resource_id'] = cpu_resource['id']
    cpu_notification_to_resource = httpx.put(
        url='http://localhost:8000/notification',
        headers={'Authorization': f'Bearer {token}'},
        json=cpu_notification_assign
    )
    cpu_notification_to_resource.raise_for_status()
    cpu_notification_to_resource = cpu_notification_to_resource.json()
    print(json.dumps(cpu_notification_to_resource, indent=4))


    print('Thats all.')


if __name__ == '__main__':
    main()
