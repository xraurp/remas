#!/bin/sh

podman pull docker.io/prom/node-exporter:v1.9.0
podman pull docker.io/ncabatoff/process-exporter:sha-b2740a6

mkdir -p /etc/prometheus-process-exporter
mkdir -p /etc/prometheus-node-exporter

cp process-exporter-config/process-exporter-config.yml /etc/prometheus-process-exporter

cp -t /etc/systemd/system/ prometheus-node-exporter.service prometheus-process-exporter.service
cp -t /usr/local/bin/ prometheus-node-exporter.sh prometheus-process-exporter.sh

systemctl enable prometheus-node-exporter
systemctl enable prometheus-process-exporter

systemctl start prometheus-node-exporter
systemctl start prometheus-process-exporter
