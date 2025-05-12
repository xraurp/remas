# Resource Usage Monitoring and Management System

Resource usage monitoring and management system for smaller computer clusters.

Name `remas` is derived from first two letters of words `resource` and `management` and first letter from `system`.


### Running the docker compose

In order for Grafana to start correctly, the folder where grafana keeps its data must be owned by user with id 472.

For prometheus, the data folder must be owned bu user:group nobody:nobody (uid:gid 65534:65534).



Initial configuration can be done using `init_db.py` script in `main_app`.

In order to make grafana work, first login using the default credential is needed.
Credentials for admin account needs to be entered to `main_app` config file.
Then `init_grafana.py` can be used to setup admin in grafana.

Datasource in grafana must be added manually. Goto Connections -> Datasource -> Prometheus and add prometheus url and login credentials.


