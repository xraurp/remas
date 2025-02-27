#!/bin/sh

podman rm prometheus-node-exporter

podman run --rm \
    -p 9100:9100 \
    --pid host \
    --network host \
    -v /:/rootfs:ro,rslave \
    --name prometheus-node-exporter \
    prom/node-exporter:v1.9.0 \
    --path.rootfs /rootfs
