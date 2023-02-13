#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "This script have to be run as root"
  exit
fi

echo 'Installing adisconcurrent and adistools...'

apt-get install curl gnupg apt-transport-https python3 python3-pip nginx uwsgi -y
pip3 install flask psutil tabulate colored pika pymongo pyyaml 

#rabbitmq and erlang keys
curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" |  gpg --dearmor |  tee /usr/share/keyrings/com.rabbitmq.team.gpg > /dev/null
curl -1sLf "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xf77f1eda57ebb1cc" |  gpg --dearmor |  tee /usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg > /dev/null
curl -1sLf "https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey" |  gpg --dearmor |  tee /usr/share/keyrings/io.packagecloud.rabbitmq.gpg > /dev/null

#mongo keys
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -

#rabbitmq repo
tee /etc/apt/sources.list.d/rabbitmq.list <<EOF
## Erlang
deb [signed-by=/usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg] http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu bionic main
deb-src [signed-by=/usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg] http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu bionic main

## RabbitMQ
deb [signed-by=/usr/share/keyrings/io.packagecloud.rabbitmq.gpg] https://packagecloud.io/rabbitmq/rabbitmq-server/ubuntu/ bionic main
deb-src [signed-by=/usr/share/keyrings/io.packagecloud.rabbitmq.gpg] https://packagecloud.io/rabbitmq/rabbitmq-server/ubuntu/ bionic main
EOF

#mongo repo
tee /etc/apt/sources.list.d/mongodb-org-6.0.list <<EOF
deb http://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main
EOF

#update database of package manager
apt-get update -y

#install erlang
apt-get install -y erlang-base \
                        erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
                        erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
                        erlang-runtime-tools erlang-snmp erlang-ssl \
                        erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl

#install rabbitmq
apt-get install rabbitmq-server -y --fix-missing

#create rabbitmq account and set permissions
rabbitmqctl add_user adisconcurrent devpasswd
rabbitmqctl set_user_tags adisconcurrent administrator
rabbitmqctl set_permissions -p / adisconcurrent ".*" ".*" ".*"

#enable rabbitmq managment
rabbitmq-plugins enable rabbitmq_management

#install mongodb
apt-get install -y mongodb-org

#enable start of mongodb on boot
systemctl enable mongod.service

#creating configurations dirs
mkdir /etc/adisconcurrent
mkdir /etc/adisconcurrent/uwsgi

mkdir /etc/adistools-api
mkdir /etc/adistools-pixel_tracker

#creating residential dirs 
mkdir /srv/adistools-api
mkdir /srv/adistools-pixel_tracker

#create dirs for adisconcurrent
mkdir /usr/lib/adisconcurrent
mkdir /usr/lib/adisconcurrent-workers
mkdir /var/log/adisconcurrent

#adding domains bindings for hosts file
echo "127.0.0.1        adistools" >>/etc/hosts
echo "127.0.0.1        pixel_tracker" >>/etc/hosts

#create site file for adistools-api
tee /etc/nginx/sites-enabled/adistools-api <<EOF
server {
        listen 80;
        server_name adistools;
        location /api {
                uwsgi_pass 127.0.0.1:9999;
                include uwsgi_params;
        }

#       location / {
#               proxy_pass http://localhost:8080;
#       }
}
EOF

#create site file for adistools-pixel_tracker
tee /etc/nginx/sites-enabled/adistools-pixel_tracker <<EOF
server {
        listen 80;
        server_name pixel_tracker;

        location / {
                uwsgi_pass 127.0.0.1:10000;
                include uwsgi_params;
        }
}
EOF

#restarting nginx
service nginx restart

#creating ini file for adistools-api
tee /etc/adisconcurrent/uwsgi/adistools-api.ini <<EOF
[uwsgi]
socket=127.0.0.1:9999
wsgi-file=__main__.py
chdir=/srv/adistools-api
single-interpreter=true
enable-threads=true
master=false
EOF

#creating ini file for adistools-pixel_tracker
tee /etc/adisconcurrent/uwsgi/adistools-pixel_tracker.ini <<EOF
[uwsgi]
socket=127.0.0.1:10000
wsgi-file=__main__.py
chdir=/srv/adistools-pixel_tracker
#single-interpreter=true
enable-threads=true
master=False
EOF

#create config for adisconcurrent
tee /etc/adisconcurrent/config.yaml <<EOF
general:
    daemonize: true
    workers_directory: /usr/lib/adisconcurrent-workers

log:
    debug: false
    logs_directory: /var/log/adisconcurrent/

daemon:
    pid_file: /var/run/adisconcurrent.pid

uwsgi:
    ini_directory: /etc/adisconcurrent/uwsgi
    uwsgi_executable_path: /usr/local/bin/uwsgi
    uid: 33
    gid: 33

rabbitmq:
    host: localhost
    port: 5672
    vhost: /
    user: adisconcurrent
    passwd: devpasswd

tasks:
    interval: 0.1
EOF

# create config file for adistools-api
tee /etc/adistools-api/config.yaml <<EOF
mongo:
    host: localhost
    port: 27017
    db: adistools
EOF

# create config file for adistools-pixel_tracker
tee /etc/adistools-pixel_tracker/config.yaml <<EOF
mongo:
    host: localhost
    port: 27017
    db: adistools

class rabbitmq:
    host: localhost
    port: 5672
    vhost: /
    user: adisconcurrent
    passwd: devpasswd
EOF

