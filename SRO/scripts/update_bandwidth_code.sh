DURATION=$1
NEW_RATE=$2

sudo tc qdisc add dev ens3 root tbf rate "$NEW_RATE" latency 1ms burst 10000
echo "sudo tc qdisc del dev ens3 root tbf rate $NEW_RATE latency 1ms burst 10000" | at now + $DURATION minutes