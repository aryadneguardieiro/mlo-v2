IP=$1
DURATION=$2
NEW_RATE=$3

PASSWORD="necos"
USERNAME="cloud"

sshpass -p "$PASSWORD" ssh -t -oStrictHostKeyChecking=no $USER@$IP rm update_bandwidth_code.sh 
sshpass -p "$PASSWORD" scp update_bandwidth_code.sh $USERNAME@$IP:~
sshpass -p "$PASSWORD" ssh -t -oStrictHostKeyChecking=no $USER@$IP "echo $PASSWORD | sudo -S sh update_bandwidth_code.sh $DURATION $NEW_RATE"
#sshpass -p $PASSWORD ssh -t -oStrictHostKeyChecking=no $USERNAME@$IP 
