#!/bin/sh

podman rm prometheus-process-exporter || true

podman run --rm \
    -p 9256:9256 \
    --privileged \
    -v /proc:/host/proc \
    -v /etc/prometheus-process-exporter:/config \
    --name prometheus-process-exporter \
    ncabatoff/process-exporter:sha-b2740a6 \
    --procfs /host/proc \
    -config.path /config/process-exporter-config.yml
