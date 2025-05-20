# Resource Usage Monitoring and Management System

Resource usage monitoring and management system for smaller computer clusters.

Name `remas` is derived from first two letters of words `resource` and `management` and first letter from `system`.

Frontend of the application is available at [this repository](https://github.com/xraurp/remas-ui).

Information about this repository content as well as API description are in chapter [Development](#development).

## Chapters

- [Running the app](#running-the-app) - shows configuration options and how to build and run the app.
- [Using the app](#using-the-app) - explains basic usage of the application.
- [Development](#development) - contains this repository structure and API documentation informations.

## What can it be used for?

Application is intended to be used as computing cluster manager. It provides calendar like interface for scheduling user tasks. User can select resources (like number of CPU cores, Memory, etc.) and nodes (computers) he wants to use. Then he can select time in calendar when he wants to have these resources reserved on selected nodes.

Application also allows administrator to create templates for Grafana alerts. These are watching over the user and notifies him if he exceeds resources which he selected for the task. Administrator can add aditional configuration using Grafana alert rules to send these notifications to other users as well (like himself to stay informed about who exeeded the resources).

Cluster monitoring is done by Prometheus and Grafana which allows monitoring a wide range of resources. For monitoring to work, Prometheus exporters must be installed on the nodes and Prometheus must be configured to scrape data from these exportes. Example configuration and install scripts for some exporters is available in `prometheus` directory.

Application services, including Prometheus server and Grafana, can be started using docker compose command - following chapters.

## What it can't be used for?

This application is not replacement for batch schedulers like Slurm. It cannot automatically start user tasks. All it does is, it allows user to reserve resources on the nodes for specific time. User must start the task himself, use the cluster interactively, or use cron to run some commands.

Application is meaned to be tool for user coordination. It helps multiple users that uses shared cluster resources to plan their tasks. It's useful for preventing overloading the nodes with too many simultaneously running processes that uses too many resources.


# Running the app

## Setup environment variables

Following variables can be used to configure the application.

- `DEBUG` - enables some additional debug output (default: False)
- `DATABASE_URL` - URL for the database (default: postgresql://remas_main:test123@localhost:15432/remas_main_db)
- `HOST` - IP address / host name on which the port will listen (default: 0.0.0.0)
- `PORT` - Application port (default: 8000)
- `SECRET_KEY` - secret key for signing JWT tokens (required)
- `ALGORITHM` - secret key signing algoritm (default: HS256)
- `TOKEN_ACCESS_EXPIRE_MINUTES` - access token expiration in minutes (default: 30)
- `TOKEN_REFRESH_EXPIRE_MINUTES` - refresh token expiration in minutes (default: 120)
- `TASK_SCHEDULER_PRECISION_SECONDS` - tells the scheduler how many secconds to the future it can plan. Highter amount results in inacurate task starts and ends. Lower amount results in higher potential load on database due to more frequent checks. (default: 60)
- `TASK_SCHEDULER_RETRY_LIMIT_SECONDS` - Number of seconds that task scheduler will wait until retrying failed operation. (default: 120)
- `SMTP_HOST` - SMTP server for sending emails to users (default: localhost)
- `SMTP_PORT` - SMTP server port (default: 465)
- `SMTP_USER` - SMTP server user (email account) (default: None)
- `SMTP_PASSWORD` - SMTP server password (default: None)
- `SMTP_ENABLED` - enables / disables SMTP (default: False)
- `SMTP_FROM_ADDRESS` - SMTP address from which the mails are send (default: same as `SMTP_USER`)
- `SMTP_FROM_NAME` - SMTP user name (default: REMAS)
- `SMTP_STARTTLS_ENABLED` - enables STARTTLS protocol (default: False)
- `GRAFANA_URL` - URL pointing to Grafana server (default: http://localhost:3000/)
- `GRAFANA_REDIRECT_URL` - used for redirecting user from fronend to Grafana instance. If app is running in docker container, it typically uses docker dns record to access Grafana. This record does not work outside the container. Thanks to this diferent URL is needed to redirect user. (default: `GRAFANA_URL`)
- `GRAFANA_USERNAME` - Grafana admin username (default: admin)
- `GRAFANA_PASSWORD` - Grafana admin password (default: admin)

There is also example script at `main_app/example_env_vars.sh`.
If there is `env_vars.sh` present in the `main_app` direcotry, then this script is sourced when app starts. Same happens if `env_vars.sh` is mounted to `/remas/env_vars.sh` when using docker container.

## Pre start-up configuration

In order for Grafana to start correctly, the folder where grafana keeps its data must be owned by user with id 472.
By default the data folder is `grafana-data/data`.

For prometheus, the data folder must be owned bu user:group nobody:nogroup (uid:gid 65534:65534).
Default folder: `prometheus-data/data`. Also modify the config in `prometheus/prometheus` and add following lines for each node that will be managed by the system:

```yaml
- job_name: process_exporter_node_name
  static_configs:
  - targets: ['remas-prometheus-process-exporter:9256']
    labels:
      node: node_name
- job_name: node_exporter_node_name
  static_configs:
  - targets: ['remas-prometheus-node-exporter:9100']
    labels:
      node: node_name
```

Also add config for any other exporters that you want to use on the node.

## Start the app

To start the application, including Grafana and Prometheus, use the `services.yaml` file.
Grafana SMTP configuration have to be provided via config file. Example configuration is in `example-smtp.conf`.
Also `env_vars.sh` is expected in the project root folder, [see chapter Setup environment variables](#Setup-environment-variables).

Before starting, goto remas app container in the compose file and change the timezone to your region. Otherwise the time based events will happen in diferent time due to timezone diference. If no timezone is specified, UTC is used. Preconfigured timezone is Europe/Prague (CET/CEST).

To run the services use following command, that will start then as docker containers:

```shell
docker compose --env-file smtp.conf -f services.yaml up -d
```

To stop the services use:

```shell
docker compose --env-file smtp.conf -f services.yaml down
```

You can also start the app manually. First setup environment using following commands in `main_app` dir:

```shell
python3 -m venv .venv
. ./.venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

App can be started by running following command:

```shell
sh run_app.sh
```

## Post start-up configuration

Initial configuration can be done using `init_db.py` script in `main_app` as so:

```shell
./init_db.py --drop --init --init-data
```

In order to make grafana work, first login using the default credentials and change them.
Credentials for admin account needs to be entered to `main_app` config file.
This can be done eighter directly in `main_app/src/config.py` or by assigning to shell variables `GRAFANA_USERNAME` and `GRAFANA_PASSWORD`.
(Or using `main_app/env_vars.sh` where all variables can be placed and loaded before the app starts. Example file is provided in same location.)
Then `init_grafana.py` can be used to setup admin in grafana.
This should be done after the main app is initiated using `init_db.py`.

```shell
./init_grafana.py
```

Datasource in grafana must be added manually. Goto Connections -> Datasource -> Prometheus and add prometheus url and login credentials.

## Frontend

Frontend is available at [this repository](https://github.com/xraurp/remas-ui). It requires node.js to be build from typescript. Then it can be served as website using node.js.

## Building the container manually

Container is build automatically when using the docker compose.
To build `main_app` container manually, use

```shell
docker build -t remas .
```

## Production setup

To use the application in production it usually requires certificates to provide HTTPS connection. Since the backend is written in FastAPI, it does not directly support HTTPS. TLS Termination Proxy application (like Nginx) have to be placed as intermediator that provides encryption. If Nginx or Apache web server is used, then it can be also used to serve the frontend files.

Frontend files are available in `dist/spa` directory after build finishes.

For more information about setting up TLS proxy see FastAPI documentation on [this link](https://fastapi.tiangolo.com/deployment/https/).


# Using the app

Basic use is described at the start of this README. Here are some more detailed information about specific parts of the application.

## Scheduling tasks

Users can schedule tasks on task page using the `add task`. Scheduling procedure is as follows:

1. User selects resources he wants to use. This is done in the left column, there is a dropdown menu on top where resources are listed.
2. Then calendar displays times when selected resources are already in use by other users. It shows nodes on which resources are not available at given time and contact info about users using them. This helps user to select nodes where resources are available. He can also schedule his task on time when there is no conflict with tasks of other users.
3. User selects nodes he wants to use. This is done in the left column under the resource dropdown.
4. User selects time when he wants to use selected resources on selected nodes by clicking on given time at calendar. In the detail of the calendar event that is created he can specify task name and also modify task duration.
5. User selects `Schedule task` button at the bottom of the page.
- User can also cancel task creation by selecting `Cancel`.

## Administration

Administrator can manage users, groups and cluster nodes and resources.

Each user must have username (matching his username on nodes), email and UID (user ID on nodes). These information are used to identify user on nodes and to send notifications about his activity.

Each user is member of exactly one group. Group is used more like user template, so admin does not have to assign restrictions and notifications directly to each user. Group can inherit configuration from one parent group.

Default groups are `Everyone`, `Administrators`, and `Users`, where the later two inherit from group `Everyone`. Each member of `Administrators` group is administrator. Also all members of groups that inherits from `Administrators` is also admins.

Administrator can define usage limits. When assigned to user, it restricts maximum amount of specified resource that the user can allocate at once. Limit can be assigned to user or group.

Administrator can also create notifications. Notification can notify user via email about starting or ending tasks.

Another type of notification is Grafana alert. There are two types:

- `Resource exceedance` - this type of notification adds alert rule to grafana that notifies user when he exceeds reserved amount of certain resource on certain node. The amount in this type of notification is fixed, defined by administrator.
- `Resource exeedance during task` - this type of notification also adds Grafana alert. In this case administrator specifies default amount of the resource the notification alerts about. User can use given resource up to this amount without scheduling a task. When he wants to use resources abow this amount, he can schedule task and specify higher amount. Then during the task the resource amount his set to user specified value. Notification is send to user only when he exceeds this amount he specified.

## Notification templates

Templates for time based notifications, that notifies about things like task start time, can use following variables:

- `user_id` - id of the task owner
- `user_name` - task owner name
- `user_surname` - task owner surname
- `user_username` - task owner username (used on the nodes to login)
- `user_uid` - task owner UID (User ID on the nodes)
- `user_email` - task owner email
- `task_id` - task id
- `task_name` - name of the task
- `task_description` - description of the task
- `task_start` - time when the task starts
- `task_end` - time when the task ends

Variable name must be enclosed in curly brackets and prefixed with dollar sign.
Example of notification template content:

```
Task ${task_name} starts in 10 minutes!
```

If the template is for Grafana alerts then it uses following variables:

- `user_id` - id of the task owner
- `user_name` - task owner name
- `user_surname` - task owner surname
- `user_username` - task owner username (used for login on nodes)
- `user_uid` - task owner UID (User Id used to identiry user on nodes)
- `user_email` - task owner email
- `node_id` - id of node that the notification informs about
- `node_name` - name of the node (usually hostname or ip address)
- `node_description` - description of the node
- `resource_id` - id of the resource that the notification informs about
- `resource_name` - name of the resource
- `resource_description` - resource description
- `resource_amount` - resource amount
- `allocation_amount` - resource amount that is allocated by the user

Variable name must be enclosed in curly brackets and prefixed with dollar sign.
Notification template for exceeding CPU cores amount and Memory amount are available in `grafana_templates` folder.
Example of notification template content (CPU notification template):

```JSON
{
    "id": null,
    "uid": null,
    "orgID": 1,
    "folderUID": "",
    "ruleGroup": "Task limit alerts",
    "title": "User ${user_username} CPU threshold on node ${node_name}",
    "condition": "CPU Usage Threshold",
    "noDataState": "NoData",
    "execErrState": "Error",
    "for": "5m",
    "annotations": {
        "summary": "User ${user_username} exceeded CPU limit on node ${node_name}! Maximum limit is ${allocation_amount}."
    },
    "labels": {},
    "isPaused": false,
    "notification_settings": {},
    "record": null,
    "data": [
        {
            "refId": "CPU Usage",
            "queryType": "",
            "relativeTimeRange": {
                "from": 600,
                "to": 0
            },
            "datasourceUid": "aejzco4xpvcw0b",
            "model": {
                "disableTextWrap": false,
                "editorMode": "builder",
                "expr": "sum by(node) (rate(namedprocess_namegroup_cpu_seconds_total{node=\"${node_name}\", groupname=\"${user_uid}\"}[1m]))",
                "fullMetaSearch": false,
                "includeNullMetadata": false,
                "instant": true,
                "intervalMs": 1000,
                "legendFormat": "__auto",
                "maxDataPoints": 43200,
                "range": false,
                "refId": "CPU Usage",
                "useBackend": false
            }
        },
        {
            "refId": "CPU Usage Threshold",
            "queryType": "",
            "relativeTimeRange": {
                "from": 0,
                "to": 0
            },
            "datasourceUid": "__expr__",
            "model": {
                "conditions": [
                    {
                        "evaluator": {
                            "params": [${allocation_amount}],
                            "type": "gt"
                        },
                        "operator": {
                            "type": "and"
                        },
                        "query": {
                            "params": ["C"]
                        },
                        "reducer": {
                            "params": [],
                            "type": "last"
                        },
                        "type": "query"
                    }
                ],
                "datasource": {
                    "type": "__expr__",
                    "uid": "__expr__"
                },
                "expression": "CPU Usage",
                "intervalMs": 1000,
                "maxDataPoints": 43200,
                "refId": "CPU Usage Threshold",
                "type": "threshold"
            }
        }
    ]
}
```

## Getting grafana templates

Grafana templates can be exported from Grafana over API. There is a script available - `scripts/get_grafana_alert.py`, that allows this.

Grafana provides user frendly interface for creating notifications. When notification is created, its `uid` can be obtained using the export button. Then pass the uid to the script and specify location where the otput should be saved. 

Resulting file can be modified into template using the variables listed in previous section.

Beware to use the notification exported using the export button! Unfortunately the format is not compatible with the Grafana HTTP API format. So it cannot be currently used to create notification template in the application.

## Using Grafana

Grafana instance is accessible via tab called `Cluster status` in left panel in the application.
Administrator can use it to identify users that exceeded resources during their tasks. This can be done in tab `Alert rules`, where triggered alerts are shown. Admin can also create notification policies that to receive emails about resource exceedance. By default only the user who exceeded the resource is notificed. This is to prevent sending alerts to admins who don't handle resource exceedances.

Admins can also create dashboards that visualize resource statistics, etc. Users can then access these dashboards and see current cluster status.

By default users are synchronized between the REMAS app and Grafana. User management should be done primarily in REMAS app. In Grafana only specific things that are not synchronized should be configured.

## Using Prometheus

Prometheus is the tool used to gather statistics from nodes.
In order for notifications to work, Prometheus must be set-up to provide usage data.
Server configuration is available in folder `prometheus/prometheus`.

Following lines are required for each node in order to use process exporter and node exporter data in grafana:

```yaml
- job_name: process_exporter_node_name
  static_configs:
  - targets: ['remas-prometheus-process-exporter:9256']
    labels:
      node: node_name
- job_name: node_exporter_node_name
  static_configs:
  - targets: ['remas-prometheus-node-exporter:9100']
    labels:
      node: node_name
```

`node_name` must match node name used for identifying the node in the app. Otherwise node will not be recognized and notifications would not work.
Process exporeter is required for CPU and memory notification templates in `grafana_templates` folder.


# Development

## Repository content

- `dockerfile` - file for creating docker container for `main_app` - API of the REMAS application
- `main_app` - directory containing main application code
    - `env_vars.sh` - script with environment variables
    - `requirements.txt` - file with python3 libraries app is dependent on
    - `init_*` - init files used when the app runs for the first time [(see this chapter)](#Post-start-up-configuration).
    - `run_app.sh` - script for starting the app
    - `run.py` - runs the app (called by `run_app.sh`) directly without loading `env_vars.sh`
    - `scripts` - contains additional script for the app (does things like accessing Grafana API, etc.)
    - `src` - contains application code
        - `app_logic` - contains app logic code and more advanced authorization
        - `routes` - contains API endpoints
        - `schemas` - contains schemas of API endpoint input and output formats
        - `db` - containst database schema and code that handle DB connections
    - `tests` - contains some of the scripts used during API testing.
- `grafana_templates` - contains some templates that can be used for defining notifications in Grafana
- `prometheus` - contains configuration for Prometheus monitoring platform
    - `process-exporter-config` - contains configuration for `process-exporter` that can be used to monitor CPU and memory on nodes
    - `prometheus` - contains example configuration for Prometheus server. Can be used to scrape statistics from exporters (after changing target nodes URLs).
    - `prometheus-*-exporter.sh` - script for running specified exporter
    - `prometheus-*-exporter.service` - systemd service file for given exporter
    - `install-exporters.sh` - script for installing exporters on linux system. Target system must have podman installed and must use systemd as system daemon. User typically needs to be root (admin) to run this script.
- `services.yaml` - docker-compose file for running the app and all its services.
- `smtp.conf` - config containing SMTP settings for Grafana

## API documentation

API documentation is available at `docs-html` folder. If API is running, it can be viewed at `/docs` endpoint.

## Frontend

Frontend of the application is available at [this repository](https://github.com/xraurp/remas-ui).
