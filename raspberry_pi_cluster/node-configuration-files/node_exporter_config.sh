#!/bin/bash

cd ~
mkdir Node\ Exporter;
chmod 775 Node\ Exporter;
cd Node\ Exporter;

line="9";
curl -LO "https://github.com/prometheus/node_exporter/releases/download/v0.17.0/node_exporter-0.17.0.linux-amd64.tar.gz"

if [ "$?" -eq "0" ]; then
	tar -zxvf node_exporter-0.17.0.linux-amd64.tar.gz;
	line="14";
	sudo mv ./node_exporter-0.17.0.linux-amd64/node_exporter /usr/local/bin/;
	if [ "$?" -eq "0" ]; then
		user_node_exporter=$(id -u node_exporter);
		if [ "$?" -eq "1" ]; then
			sudo useradd node_exporter;
		fi
		
		sudo chown node_exporter:node_exporter /usr/local/bin/node_exporter;
		
		line="24";
		echo -e "[Unit]\nDescription=Node Exporter\nWants=network-online.target\nAfter=network-online.target\n\n[Service]\nUser=node_exporter\nGroup=node_exporter\nType=simple\nExecStart=/usr/local/bin/node_exporter\n\n[Install]\nWantedBy=multi-user.target\n" | sudo tee /etc/systemd/system/node_exporter.service;
		if [ "$?" -eq "0" ]; then
			sudo systemctl daemon-reload;
			sudo systemctl start node_exporter;
			rm -r ./node_exporter-0.17.0.linux-amd64;
			echo -e "Configuracao feita com sucesso. Execute \"sudo systemctl status node_exporter\" para ver o status do servico.\nSe estiver tudo certo, atualize o config_map do prometheus com o IP: $(hostname -I)";
			exit 0;
		fi
	fi
fi
echo "Erro na execucao do script. Rever linha $line";
