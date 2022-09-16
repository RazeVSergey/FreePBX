#!/bin/bash

set -o pipefail

install_packet(){
  
#Install components
apt-get update && apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release -y 

#Add Docker’s official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg   |  apt-key add -

#up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update && apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

#Create the docker group
groupadd docker

#Add your user to the docker group
usermod -aG docker ${USER}


#Istall docker compose
curl -SL https://github.com/docker/compose/releases/download/v2.6.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
chmod +x /usr/bin/docker-compose

}

#Check install packet
response=`dpkg -l | grep -e 'docker|container' | awk '{print $2}'`

[ -z "$response" ]  && install_packet;
