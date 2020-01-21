OPERATION=$1
IP=$2
RATE=$3
PASSWORD="necos"
USER="cloud"

sshpass -p $PASSWORD ssh -q -t -oStrictHostKeyChecking=no $USER@$IP > /dev/null 2>&1 << EOF
  echo $PASSWORD | sudo -S tc qdisc $OPERATION dev ens3 root tbf rate "$RATE" latency 1ms burst 10000
EOF
