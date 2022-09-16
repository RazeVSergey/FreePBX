#!/bin/bash

APP_PORT_HTTP="80"
HTTPD_CONF_DIR="/etc/httpd/"

wget https://files.phpmyadmin.net/phpMyAdmin/5.1.4/phpMyAdmin-5.1.4-all-languages.zip && \
unzip phpMyAdmin-*-all-languages.zip && \
cd /usr/share/phpmyadmin && \
mv config.sample.inc.php config.inc.php && \
mkdir /usr/share/phpmyadmin/tmp && \
chown -R apache:apache /usr/share/phpmyadmin && \
chmod 777 /usr/share/phpmyadmin/tmp && \


echo "
 <VirtualHost *:${APP_PORT_HTTP}>

   Alias /phpmyadmin /usr/share/phpmyadmin
  <Directory /var/www/html>
    Options FollowSymLinks
    DirectoryIndex index.php
    AllowOverride All
  </Directory>
 </VirtualHost>
" >> ${HTTPD_CONF_DIR}/conf.d/phpMyAdmin.conf

echo "
  AuthType Basic
  AuthName "Restricted Files"
  AuthUserFile /etc/phpmyadmin/.htpasswd
  Require valid-user
" > /usr/share/phpmyadmin/.htaccess