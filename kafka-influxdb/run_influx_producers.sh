#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Usage: run_influx_producers.sh DURATION";
	exit 1;
fi

DURATION=$1
SCRIPT_PATH=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

echo "$SCRIPT_PATH"
cd $SCRIPT_PATH

echo "Running config_client_metrics";
timeout "$DURATION"m python3 -m kafka_influxdb -c config_client_metrics.yaml &
echo "Running config_estimate_sla_sro";
timeout "$DURATION"m python3 -m kafka_influxdb -c config_estimate_sla_sro.yaml &
echo "Running config_logs_sro";
timeout "$DURATION"m python3 -m kafka_influxdb -c config_logs_sro.yaml &
echo "Running config_loadgen_metrics.yaml"
timeout "$DURATION"m python3 -m kafka_influxdb -c config_loadgen_metrics.yaml &
echo "Running config_selected_metrics.yaml"
timeout "$DURATION"m python3 -m kafka_influxdb -c config_selected_metrics.yaml &
echo "Done"
