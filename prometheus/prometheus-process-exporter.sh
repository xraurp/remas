#!/bin/sh

podman rm prometheus-process-exporter

podman run --rm \
    -p 9256:9256 \
    --privileged \
    --pid host \
    -v /proc:/host/proc:ro,rslave \
    -v /etc/prometheus-process-exporter:/config \
    --name prometheus-process-exporter \
    ncabatoff/process-exporter:sha-b2740a6 \
    --procfs /host/proc \
    -config.path /config/process-exporter-config.yml
