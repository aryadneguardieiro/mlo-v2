#!/bin/sh

# to run on a remote host:
# scp chrony_config.sh USER@IP:~ && sshpass -p "password" ssh USER@IP sh chrony_config.sh

sudo apt install -y chrony && \

sudo sed -i s/pool\ 2.debian.pool.ntp.org/#\ pool\ 2.debian.pool.ntp.org/g /etc/chrony/chrony.conf && \

sudo sed -i s/makestep\ 1\ 3/makestep\ 1\ -1/g /etc/chrony/chrony.conf && \

printf "\n# This line makes cloud1 the chrony server\n" | sudo tee -a /etc/chrony/chrony.conf && \

echo "server 192.168.0.1 iburst minpoll 2 maxpoll 4" | sudo tee -a /etc/chrony/chrony.conf && \

sudo systemctl restart chrony && \

sleep 5 && \

chronyc sources
