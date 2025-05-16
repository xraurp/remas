# Resource Usage Monitoring and Management System

Resource usage monitoring and management system for smaller computer clusters.

Name `remas` is derived from first two letters of words `resource` and `management` and first letter from `system`.

### Running the docker compose

In order for Grafana to start correctly, the folder where grafana keeps its data must be owned by user with id 472.
By default the data folder is `grafana-data/data`.

For prometheus, the data folder must be owned bu user:group nobody:nogroup (uid:gid 65534:65534).
Default folder: `prometheus-data/data`.

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

### Running the app

To start the application, including Grafana and Prometheus, use the `services.yaml` file.
Grafana SMTP configuration have to be provided via config file. Example configuration is in `example-smtp.conf`.
To run the services use following command, that will start then as docker containers:

```shell
docker compose --env-file smtp.conf -f services.yaml up -d
```

To stop the services use:

```shell
docker compose --env-file smtp.conf -f services.yaml down
```
