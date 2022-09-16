#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

RUNTIME_PACKAGES="libao4 libasound2 libportaudio2 lame python3 python3-pip python3-setuptools locales opus-tools \
locales-all"
BUILD_PACKAGES="git scons python-lxml build-essential libao-dev pkg-config flite1-dev portaudio19-dev"

apt-get update -y
apt-get -y install --no-install-recommends "${RUNTIME_PACKAGES}" "${BUILD_PACKAGES}"
sudo -H python3 -m pip install --upgrade pip setuptools wheel
sudo -H python3 -m pip install flask pymorphy2 rhvoice-wrapper

cp app.py /opt/rhvoice-rest.py
cp rhvoice_rest_cache.py /opt/
chmod +x /opt/rhvoice-rest.py

git clone --depth=1 --branch 1.2.3 https://github.com/Olga-Yakovleva/RHVoice.git /opt/RHVoice
cd /opt/RHVoice && scons && scons install && ldconfig

git clone https://github.com/vantu5z/RHVoice-dictionary.git /opt/RHVoice-dictionary
mkdir -p /usr/local/etc/RHVoice/ && mkdir -p /opt/data
cp -R /opt/RHVoice-dictionary/dicts /usr/local/etc/RHVoice/dicts
cp -R /opt/RHVoice-dictionary/tools/preprocessing /opt/rhvoice_tools
cd /opt && rm -rf /opt/RHVoice /opt/RHVoice-dictionary

{
echo '[Unit]'
echo 'Description=RHVoice REST API'
echo 'After=network.target'
echo '[Service]'
echo 'ExecStart=/opt/rhvoice-rest.py'
echo 'Restart=always'
echo 'User=root'
echo '[Install]'
echo 'WantedBy=multi-user.target'
} > /etc/systemd/system/rhvoice-rest.service

systemctl enable rhvoice-rest.service
systemctl start rhvoice-rest.service
