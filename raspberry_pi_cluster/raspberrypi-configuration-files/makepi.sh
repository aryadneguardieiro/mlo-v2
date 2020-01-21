#!/bin/sh

# Creates the file of the task wich will configure network settings like hostname, static ip, and gateway ip
# $1: hostname. Ex.:cloud10
# $2: static ip. Ex.: 192.168.0.10
# $3: gateway ip. Ex.: 192.168.0.1
create_task2()
{
	hostname=$1
	ip=$2 # should be of format: 192.168.1.100
	dns=$3 # should be of format: 192.168.1.1

	echo "#!/bin/sh

		# Change the hostname
		sudo sed -i s/raspberrypi/$hostname/g /etc/hosts;
		sudo hostnamectl --transient set-hostname $hostname;
		sudo hostnamectl --static set-hostname $hostname;
		sudo hostnamectl --pretty set-hostname $hostname;

		# Set the static ip
		sudo cat <<EOT >> /etc/dhcpcd.conf
		interface eth0
		static ip_address=$ip/24
		static routers=$dns
		static domain_name_servers=8.8.8.8, 8.8.4.4
		EOT" > /home/pi/tasks/task2.sh;
}

# Creates the file of the task wich will install docker and kubeadm
create_task1() {
	echo '#!/bin/sh

		echo "LOG: started task1.sh"
		# Install Docker
		curl -sSL get.docker.com > /home/pi/tasks/getDocker.sh;
		sh /home/pi/tasks/getDocker.sh >> /home/pi/log.txt && \
		  sudo usermod pi -aG docker
		rm /home/pi/tasks/getDocker.sh;

		# Disable Swap
		sudo dphys-swapfile swapoff && \
		  sudo dphys-swapfile uninstall && \
		  sudo update-rc.d dphys-swapfile remove
		echo Adding " cgroup_enable=cpuset cgroup_enable=memory" to /boot/cmdline.txt
		sudo cp /boot/cmdline.txt /boot/cmdline_backup.txt
		# if you encounter problems, try changing cgroup_memory=1 to cgroup_enable=memory.
		orig="$(head -n1 /boot/cmdline.txt) cgroup_enable=cpuset cgroup_memory=1"
		echo $orig | sudo tee /boot/cmdline.txt

		# Add repo list and install kubeadm
		curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add - && \
		  echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list && \
		  sudo apt-get update && \
		sudo apt-get install -y kubeadm
		echo "LOG: just run install kubeadm"' > /home/pi/tasks/task1.sh;
}

# Configures the proxy for UFU
set_ufu_proxy()
{
	if [ "$( grep 'proxy.ufu.br' /etc/environment )" = "" ]; then
		printf "https_proxy=\"http://proxy.ufu.br:3128\"\nhttp_proxy=\"http://proxy.ufu.br:3128\"\nftp_proxy=\"http://proxy.ufu.br:3128\"" | sudo tee -a /etc/environment;
		echo 'Defaults env_keep += "ftp_proxy http_proxy https_proxy"' | sudo EDITOR='tee -a' visudo
	fi;

	if [ "$( grep 'proxy.ufu.br' /etc/apt/apt.conf.d/10proxy )" = "" ]; then
		echo 'Acquire::http::Proxy "http://proxy.ufu.br:3128/";' | sudo tee /etc/apt/apt.conf.d/10proxy;
	fi;
}

# Changes password
change_password()
{
	echo "pi:$1" | sudo chpasswd -c SHA512
}

# Checks if the connection with proxy server is ready
test_connection() 
{
	result=""
	while [ "$result" != "0" ]; do
		ping proxy.ufu.br -c 2 -q;
		result=$(echo $?);
		echo "Ping proxy.ufu.br -> result=$result" >> /home/pi/log.txt;
		sleep 2;
	done
}

# Runs the tasks to configure the raspbberypi: task1 for docker and kubeadm install, and set up and task2 for network settings
main_make_pi()
{
	if [ "$(ls /home/pi | grep tasks)" = "" ]; then
		crontab -r;
		(crontab -l 2>/dev/null; echo "@reboot sh /home/pi/makepi.sh") | crontab -;
		set_ufu_proxy;
		change_password $4
		mkdir /home/pi/tasks;
		create_task1;
		echo "LOG: just created task 1" >> /home/pi/log.txt;
		create_task2 $1 $2 $3;
		echo "LOG: just created task 2" >> /home/pi/log.txt;
		echo "LOG: rebootting now" >> /home/pi/log.txt;
		sudo shutdown -r now >> /home/pi/log.txt;
	else
		script_to_run=$(echo $(ls /home/pi/tasks/ | sort)" " | cut -d ' ' -f 1);
		if [ "$script_to_run" = "" ]; then
			rm -rf /home/pi/tasks;
			echo "LOG: just removed /home/pi/tasks and refreshing crontab" >> /home/pi/log.txt;
			crontab -r;
			echo "Done!! :DD" >> /home/pi/log.txt;
		else
			test_connection;
			echo "LOG: start to run $script_to_run" >> /home/pi/log.txt;
			sh /home/pi/tasks/$script_to_run >> /home/pi/log.txt 2>&1;
			echo "LOG: just executed $script_to_run" >> /home/pi/log.txt;
			rm -f /home/pi/tasks/$script_to_run;
			echo "LOG: rebootting now" >> /home/pi/log.txt;
			sudo shutdown -r now >> /home/pi/log.txt;
		fi;
	fi;
}


# Installs kubeadm, docker, configures network settings like hostname, static ip and gateway, and changes password
# $1: hostname. Ex.: cloud10
# $2: static ip. Ex.: 192.168.0.10
# $3: gateway ip. Ex.: 192.168.0.1
# $4: password. Ex.: yourPassword
main_make_pi $1 $2 $3 $4
