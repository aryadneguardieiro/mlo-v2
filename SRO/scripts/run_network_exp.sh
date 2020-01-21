IP_CLIENT=192.168.0.114
IP_LOADGEN=192.168.0.101
IPS_CASSANDRA=("192.168.0.107" "192.168.0.108" "192.168.0.109" "192.168.0.113" "192.168.0.116")
#IPS_CASSANDRA=("192.168.0.107")
IP_INFLUX_PRODUCERS=192.168.0.121

USER="cloud"
PASSWORD="necos"

DURATION_SINUSOID=20
DURATION_EXP=180
LAMBDA=5
INITIAL_CLIENTS=6
THREADS=10

BANDWIDTHS=("10Mbit" "30Mbit")
MULTIPLIER=0
LEN_BANDWIDTHS=${#BANDWIDTHS[@]}
DURATION_TOTAL=$((DURATION_EXP*LEN_BANDWIDTHS))

#Change cassandra cluster configurations
echo "Changing cassandra cluster configuration..."
for BANDWIDTH in "${BANDWIDTHS[@]}"; do
  for IP in "${IPS_CASSANDRA[@]}"; do
    echo "Scheduling $BANDWIDTH at $IP"
    echo "./update_bandwidth.sh $IP $DURATION_EXP $BANDWIDTH" | at now + $((DURATION_EXP*MULTIPLIER)) minutes
  done
  MULTIPLIER=$((MULTIPLIER+1))
done

#Start loadgen, client and loadgen metrics
#echo "Starting Kafka producers"
#echo "Duration: $DURATION_TOTAL"
#sshpass -p "$PASSWORD" ssh -f -oStrictHostKeyChecking=no $USER@$IP_INFLUX_PRODUCERS ~/projects/kafka-influxdb/run_influx_producers.sh $DURATION_TOTAL > /dev/null 2>&1 &
#echo "Starting Loadgen"
#sshpass -p "$PASSWORD" ssh -f -oStrictHostKeyChecking=no $USER@$IP_LOADGEN ~/apache-cassandra-3.11.3/tools/run_loadgen_and_kafka_exporter.sh $DURATION_TOTAL $DURATION_SINUSOID $LAMBDA $INITIAL_CLIENTS
#echo "Starting Client"
#sshpass -p "$PASSWORD" ssh -t -f -oStrictHostKeyChecking=no $USER@$IP_CLIENT ~/cassandra/tools/run_client_and_kafka_exporter.sh $DURATION_TOTAL $LAMBDA $INITIAL_CLIENTS $THREADS;
