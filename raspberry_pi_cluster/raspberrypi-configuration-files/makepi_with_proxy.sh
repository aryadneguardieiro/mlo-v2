create_task1()
{
	hostname=$1
	ip=$2 # should be of format: 192.168.1.100
	dns=$3 # should be of format: 192.168.1.1
	echo "#!/bin/sh
	
		# Change the hostname
		sudo sed -i s/raspberrypi/$hostname/g /etc/hosts
		sudo hostnamectl --transient set-hostname $hostname
		sudo hostnamectl --static set-hostname $hostname
		sudo hostnamectl --pretty set-hostname $hostname


		# Set the static ip

		sudo cat <<EOT >> /etc/dhcpcd.conf
		interface eth0
		static ip_address=$ip/24
		static routers=$dns
		static domain_name_servers=$dns
		EOT" > task1.sh

	chmod +x task1.sh
}

create_task2() {
	echo '#!/bin/sh

		# Install Docker
		curl -sSL get.docker.com | sh && \
		  sudo usermod pi -aG docker

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
		  sudo apt-get update -q && \
		  sudo apt-get install -qy kubeadm'	> task2.sh
	chmod +x task2.sh
}

set_ufu_proxy()
{
	if [ "$( grep 'proxy.ufu.br' /etc/profile )" = "" ]; then
		echo '
			export https_proxy="http://proxy.ufu.br:3128" 
			export http_proxy="http://proxy.ufu.br:3128"  
			export ftp_proxy="http://proxy.ufu.br:3128"
		' >> /etc/profile
	fi;
	
	if [ "$( grep 'proxy.ufu.br' /etc/apt/apt.conf.d/10proxy )" = "" ]; then 
		echo 'Acquire::http::Proxy "http://proxy.ufu.br:3128/";' > /etc/apt/apt.conf.d/10proxy
	fi;
}

main_make_pi() 
{

	if [ "$(ls /home/pi | grep tasks)" = "" ]; then
		(crontab -l 2>/dev/null; echo "@reboot /home/pi/makepi.sh") | crontab -
		set_ufu_proxy
		mkdir /home/pi/tasks
		cd /home/pi/tasks/
		create_task1 $1 $2 $3
		create_task2
	else
		cd /home/pi/tasks/
		script_to_run=$(echo "$(ls | sort) " | cut -d ' ' -f 1)
		if [ "$script_to_run" = "" ]; then
			cd /home/pi
			rm -rf tasks
			crontab -r
		else 
			./$script_to_run
			rm -f /home/pi/tasks/$script_to_run
		fi;
	fi;
	reboot
}

create_task1()
{
	hostname=$1
	ip=$2 # should be of format: 192.168.1.100
	dns=$3 # should be of format: 192.168.1.1
	echo "#!/bin/sh
	
		# Change the hostname
		sudo sed -i s/raspberrypi/$hostname/g /etc/hosts
		sudo hostnamectl --transient set-hostname $hostname
		sudo hostnamectl --static set-hostname $hostname
		sudo hostnamectl --pretty set-hostname $hostname


		# Set the static ip

		sudo cat <<EOT >> /etc/dhcpcd.conf
		interface eth0
		static ip_address=$ip/24
		static routers=$dns
		static domain_name_servers=$dns
		EOT" > task1.sh

	chmod +x task1.sh
}

create_task2() {
	echo '#!/bin/sh

		# Install Docker
		curl -sSL get.docker.com | sh && \
		  sudo usermod pi -aG docker

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
		  sudo apt-get update -q && \
		  sudo apt-get install -qy kubeadm'	> task2.sh
	chmod +x task2.sh
}

set_ufu_proxy()
{
	if [ "$( grep 'proxy.ufu.br' /etc/profile )" = "" ]; then
		echo '
			export https_proxy="http://proxy.ufu.br:3128" 
			export http_proxy="http://proxy.ufu.br:3128"  
			export ftp_proxy="http://proxy.ufu.br:3128"
		' >> /etc/profile
	fi;
	
	if [ "$( grep 'proxy.ufu.br' /etc/apt/apt.conf.d/10proxy )" = "" ]; then 
		echo 'Acquire::http::Proxy "http://proxy.ufu.br:3128/";' > /etc/apt/apt.conf.d/10proxy
	fi;
}

main_make_pi() 
{

	if [ "$(ls /home/pi | grep tasks)" = "" ]; then
		(crontab -l 2>/dev/null; echo "@reboot /home/pi/makepi_with_proxy.sh") | crontab -
		set_ufu_proxy
		mkdir /home/pi/tasks
		cd /home/pi/tasks/
		create_task1 $1 $2 $3
		create_task2
	else
		cd /home/pi/tasks/
		script_to_run=$(echo "$(ls | sort) " | cut -d ' ' -f 1)
		if [ "$script_to_run" = "" ]; then
			cd /home/pi
			rm -rf tasks
			crontab -r
		else 
			./$script_to_run
			rm -f /home/pi/tasks/$script_to_run
		fi;
	fi;
	reboot
}

# Install kubeadm, docker, configure network settings like hostname, static ip and gateway, and changes password
# $1: hostname. Ex.: cloud10
# $2: static ip. Ex.: 192.168.0.10
# $3: gateway ip. Ex.: 192.168.0.1
# $4: password. Ex.: yourPassword
main_make_pi $1 $2 $3
