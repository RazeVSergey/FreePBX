# FreePBX
Hello, this is the instruction to start freepbx


<!-- toc -->
* [Description](#description)
* [Features](#features)
* [Screenshots](#screenshots)
* [Targets of this project](#targets-of-this-project)
* [Limits of this project](#limits-of-this-project)
* [Deploy izPBX](#deploy-izpbx)
  * [Alternative deploy](#alternative-deploy-method-via-docker-run-command-not-suggested)
* [Upgrade izPBX](#upgrade-izpbx)
  * [Upgrade path to a major FreePBX release](#upgrade-path-to-a-major-freepbx-release)
  * [method 1](#method-1-automatic-upgrade-using-izpbx-container-release-suggested)
  * [method 2](#method-2-manual-upgrade-using-freepbx-upgrader-tool)
* [izPBX Development](#izpbx-development)
  * [Build](#build)
  * [Run](#run)
    * [Docker Run](#docker-run)
    * [Docker Compose](#docker-compose)
* [Advanced Production Configuration Examples](#advanced-production-configuration-examples)
  * [Multi-Tenant VoIP PBX with dedicated Databases](#multi-tenant-voip-pbx-with-dedicated-databases)
  * [Objective](#objective)
  * [Configuration](#configuration)
  * [Deploy](#deploy)
* [Services Management](#services-management)
  * [Restart izPBX](#command-to-restart-whole-izpbx-deploy)
  * [Restart izPBX container only](#command-to-restart-izpbx-container-only)
  * [Restart DB container only](#command-to-restart-db-container-only)
  * [Restart single services inside container](#if-you-want-restart-single-services-inside-izpbx-container)
* [Tested systems and host compatibility](#tested-systems-and-host-compatibility)
* [FreePBX Configuration Best Practices](#freepbx-configuration-best-practices)
* [Configuring VoIP](#configuring-voip-xml-phonebook-lookup)  
  * [Option 1: PhoneBook Menu](#option-1-phonebook-menu)
  * [Option 2: Define every PhoneBook you want to use](#option-2-define-every-phonebook-you-want-to-use)
* [FAQ / Troubleshooting](#faq--troubleshooting)
<!-- tocstop -->

[<img src="https://www.initzero.it/images/initzero-logo-izpbx-48x48.png">](https://www.initzero.it) izPBX Cloud Native VoIP Telephony System

# Description
izPBX is a Turnkey Cloud Native VoIP Telephony System powered by Asterisk Engine and FreePBX Management GUI


# Features
- Fast initial bootstrap to deploy a full features PBX system (60 secs install time from zero to a running turnkey PBX system)
- Built-in PBX Engine based on Asterisk® project (compiled from scratch)
- Built-in WEB Management GUI based on FreePBX® project (with default predownloaded modules for quicker initial deploy)
- No vendor lock-in, you can migrare to izPBX and away izPBX simply importing/exporting FreePBX Backups
- Based on Rocky Linux 8 64bit OS (RHEL derivate with long term support)
- Small container image footprint (~450 MB vs 2300 MB of official FreePBX ISO distro file)
- Multi-Tenant PBX System Support (look into **Advanced Production Configuration Examples** section)
- Automatic Remote XML PhoneBook support for compatible VoIP Phones
- Persistent storage mode for configuration and not volatile data
- Fail2ban as security monitor to block SIP and HTTP brute force attacks
- FOP2 Operator Panel
- Integrated Asterisk Zabbix agent for services health monitoring
- Misc `izpbx-*` tools scripts (like `izpbx-callstats`)
- `izsynth` utility - TTS/Text To Speech synthesizer, background music overlay assembler and audio file converter for PBX and Home Automation Systems
- `tcpdump` and `sngrep` utility to debug VoIP calls
- supervisord as services management with monitoring and automatic restart when services fail
- postfix MTA daemon for sending mails (notifications, voicemails and FAXes)
- Integrated cron daemon for running scheduled tasks
- Integrated TFTP and DHCP server powered by DNSMasq for autoprovisioning VoIP Phones
- Integrated NTP Server
- Apache 2.4 and PHP 7.2 (mpm_prefork+mod_php configuration mode)
- Automatic Let's Encrypt HTTPS certificate management for exposed PBXs to Internet
- Custom commercial SSL Certificates support
- Logrotating of service logs
- All configurations made via single central `.env` file
- Many customizable variables to use (look inside `default.env` file)
- Only two containers setup: (**Antipattern container design** but needed by the FreePBX ecosystem to works)
  - **izpbx** (izpbx-asterisk container: Asterisk Engine + FreePBX Frontend + others services)
  - **izpbx-db** (mariadb container: Database Backend)


# Screenshots
#### izPBX Dashboard (FreePBX):
![izpbx-dashboard](https://github.com/RazeVSergey/FreePBX/blob/main/screenshots/izpbx-dashboard.png)

#### izPBX Operator Panel (FOP2):
![izpbx-izpbx-operator-panel](https://github.com/RazeVSergey/FreePBX/blob/main/screenshots/izpbx-operator-panel.png)

#### izPBX Monitoring Dashboard (Zabbix):
![izpbx-zabbix-dashboard](https://github.com/RazeVSergey/FreePBX/blob/main/screenshots/izpbx-zabbix-dashboard.png)

#### izPBX CLI (Asterisk):
![izpbx-console](https://github.com/RazeVSergey/FreePBX/blob/main/screenshots/izpbx-cli.png)


# Targets of this project
On-Premise, fast, automatic and repeatable deploy of PBX systems.  
by default `network_mode: host` is used, so the PBX network is esposed directly in the host interface (no internal container network is used), so the default UDP RTP port range can be from `10000` to `20000`.  
If you plan to disable `network_mode: host`, tune the port range (forwarding 10000 ports with the docker stack make high cpu usage and longer startup times), for example for 50 concurrent calls:  
`APP_PORT_RTP_START=10000`  
`APP_PORT_RTP_END=10200`  
for best security, fine-tune the ports range based on your needs by not using standard port ranges!  

# Limits of this project
- Deploy 1 izPBX instance for every host. No multi deploy works out of the box by default when using `network_mode: host` (look **Advanced Production Configuration Examples** section for Multi-Tenant Solutions)
- Container Antipattern Design (FreePBX was not designed to run as containerized app, and its ecosystem requires numerous modules to function, and the FreePBX modules updates will managed by FreePBX Admin Modules Pages itself not by izPBX container updates)
  
# Deploy izPBX
Using **docker-compose** is the suggested method:

- Install your prefered Linux OS into VM or Baremetal Server

- Install Docker Runtime and docker-compose utility for your Operating System from https://www.docker.com/get-started
  - RHEL8 based distro Quick&Dirty commands (skip if you use other distribution):
```
sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install docker-ce -y
eval sudo curl -L "$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep browser_download_url | grep "docker-compose-$(uname -s)-$(uname -m)\"" | awk '{print $2}')" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
sudo systemctl enable --now docker
```

- Create a `docker-compose.yml`, or clone git repository, or download latest tarbal release from: https://github.com/ugoviti/izpbx/releases and unpack it into a directory (ex. `/opt/izpbx`), faster method with git:
  - `git clone https://github.com/ugoviti/izpbx.git /opt/izpbx`
  - `cd /opt/izpbx`

- Checkout into latest official release:
  - `git checkout tags/$(git tag | sort --version-sort | tail -1)`

- Copy default configuration file `default.env` into `.env`:
  - `cp default.env .env`

- Customize `.env` variables, specially the security section of default passwords:
  - `vim .env`

- Deploy and start izpbx using docker-compose command:
  - `docker-compose up -d`

- Wait the pull to finish (~60 seconds with fast internet connections) and point your web browser to the IP address of your docker host and follow initial setup guide

**Note:** by default, to correctly handle SIP NAT and SIP-RTP UDP traffic, the izpbx container will use the `network_mode: host`, so the izpbx container will be exposed directly to the outside network without using docker internal network range (**network_mode: host** will prevent multiple izpbx containers from running inside the same host).  
Modify docker-compose.yml and comment `#network_mode: host` if you want run multiple izpbx containers in the same host (not production tested. There will be problems with RTP traffic).
Another available option is to disable `network_mode: host` and use **macvlan** network mode used for running izPBX into multi-tenant mode.

## Alternative deploy method via 'docker run' command (not suggested)
If you want test izPBX without using docker-compose, you can use the following docker commands:

1. Start MySQL:  
`docker run --rm -ti -v ./data/db:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=CHANGEM3 -e MYSQL_PASSWORD=CHANGEM3 --name izpbx-db mariadb:10.4`

2. Start izPBX:  
`docker run --rm -ti --network=host --privileged --cap-add=NET_ADMIN -v ./data/izpbx:/data -e MYSQL_ROOT_PASSWORD=CHANGEM3 -e MYSQL_PASSWORD=CHANGEM3 -e MYSQL_SERVER=127.0.0.1 -e MYSQL_DATABASE=asterisk -e MYSQL_USER=asterisk -e APP_DATA=/data --name izpbx izpbx-asterisk:latest`

# Upgrade izPBX

1. Upgrade the version of izpbx by downloading a new tgz release, or changing image tag into **docker-compose.yml** file (from git releases page, verify if upstream docker compose was updated), or if you cloned directly from GIT, use the following commands as quick method:
```
cd /opt/izpbx
git checkout main
git pull
git fetch --tags --all -f
git checkout tags/$(git tag | sort --version-sort | tail -1)
```

2. Upgrade the **izpbx** deploy with:  
(NB. **First** verify if `docker-compose.yml` and `default.env` was updated a make the same changes in your `.env` file)
```
docker-compose pull
docker-compose up -d
```

3. If the mariadb database version was changed, rememeber to update tables schema with command  
  `source .env ; docker exec -it izpbx-db mysql_upgrade -u root -p$MYSQL_ROOT_PASSWORD`

4. Open FreePBX Web URL and verify if exist any modules updates from FreePBX Menù: **Admin --> Modules Admin --> Check Online --> Upgade all --> Process**

That's all

### Upgrade path to a major FreePBX release
FreePBX will be installed into persistent data dir on initial deploy only (when no installations already exist).

Successive container updates on the same release (example from 18.15.1 to 18.15.2) will not upgrade the FreePBX Framework (only Asterisk engine will be updated).  

If you want upgrade FreePBX Framework/Core to a major release (example from 15 to 16), you have 2 options:  
  
1. Automatic upgrade using izPBX container release (example, switching from 18.15.x to 18.16.x release)
2. Manual upgrade using **FreePBX Upgrader** tool

### method 1: Automatic upgrade using izPBX container release (suggested)
* Make sure before switching izPBX to a new major release, all FreePBX modules are updated to the latest release
* Make sure you made a full backup of `data` dir (IMPORTANT!)
* Make sure you enabled `FREEPBX_AUTOUPGRADE_CORE=true` in the `.env` file
* Deploy the latest version of izPBX (ex. 18.15.x for FreePBX 15, 18.16.x for FreePBX 16, etc...)
* izPBX should be detect an old FreePBX version installed and start the upgrade process
* From the **FreePBX / Modules Admin** page, check if all modules are been updated and enable again disabled modules

### method 2: Manual upgrade using FreePBX Upgrader tool
* Make sure before switching izPBX to a new major release, all FreePBX modules are updated to the latest release
* Make sure you made a full backup of `data` dir (IMPORTANT!)
* Make sure you disabled `FREEPBX_AUTOUPGRADE_CORE=false` in the `.env` file
* Deploy the latest version of izPBX (ex. 18.15.x for FreePBX 15, 18.16.x for FreePBX 16, etc...)
* izPBX should start with the old FreePBX release but with all dependences installed and ready to complete the upgrade
* Open FreePBX Menù: **Admin --> Modules Admin --> Check Online** select **FreePBX Upgrader --> Process**
* Follow these istructions: https://wiki.freepbx.org/display/FOP/Non+Distro+-+Upgrade+to+FreePBX+16
* From the **FreePBX / Modules Admin** page, check if all modules are been updated and enable again disabled modules


# izPBX Development

## Build

Asterisk 18 + FreePBX 16:  
`docker build --pull --rm --build-arg APP_DEBUG=1 --build-arg APP_VER_BUILD=1 --build-arg APP_BUILD_COMMIT=0000000 --build-arg APP_BUILD_DATE=$(date +%s) --build-arg APP_VER=dev-18.16 --build-arg FREEPBX_VER=16 -t izpbx-asterisk:dev-18.16 .`

Asterisk 18 + FreePBX 15:  
`docker build --pull --rm --build-arg APP_DEBUG=1 --build-arg APP_VER_BUILD=1 --build-arg APP_BUILD_COMMIT=0000000 --build-arg APP_BUILD_DATE=$(date +%s) --build-arg APP_VER=dev-18.15 --build-arg FREEPBX_VER=15 -t izpbx-asterisk:dev-18.15 .`


## Run

### Docker Run:
Start MySQL:  
`docker run --rm -ti -p 3306:3306 -v ${PWD}/data/db:/var/lib/mysql -e MYSQL_DATABASE=asterisk -e MYSQL_USER=asterisk -e MYSQL_ROOT_PASSWORD=CHANGEM3 -e MYSQL_PASSWORD=CHANGEM3 --name izpbx-db mariadb:10.6`

Start izPBX:  
`docker run --rm -ti --network=host --privileged --cap-add=NET_ADMIN -v ${PWD}/data/izpbx:/data -e MYSQL_SERVER=127.0.0.1 -e MYSQL_DATABASE=asterisk -e MYSQL_USER=asterisk -e MYSQL_ROOT_PASSWORD=CHANGEM3 -e MYSQL_PASSWORD=CHANGEM3 -e APP_DATA=/data --name izpbx izpbx-asterisk:dev-18.16`


### Docker Compose:

Asterisk 18 + FreePBX 16:  
`docker-compose down ; docker-compose -f docker-compose.yml -f docker-compose-dev-18.16.yml up`

Asterisk 18 + FreePBX 15:  
`docker-compose down ; docker-compose -f docker-compose.yml -f docker-compose-dev-18.15.yml up`

# Advanced Production Configuration Examples

### Multi-Tenant VoIP PBX with dedicated Databases

#### Objective
- Run many izPBX instances into single docker host (you must allocate an external static IP for every izPBX backend/frontend)
- Dedicated Database for every izPBX instances

#### Configuration
Create a directory where you want deploy izpbx data and create `docker-compose.yml` and `.env` files:

Example:
```
mkdir yourgreatpbx
cd yourgreatpbx
vim docker-compose.yml
vim .env
```

NOTE:
- Modify `docker-compose.yml` according to your environment needs:
  - `parent:` (must be specified your ethernet card)
  - `subnet:` (must match you intranet network range)
  - `ipv4_address:` (every izPBX frontend will must to have a different external IP)
- Modify `.env` according to your environment needs:
  - `MYSQL_SERVER=db` (you can't use localhost here)

```yaml
version: '3'

networks:
  izpbx-0-ext:
    driver: macvlan
    driver_opts:
      parent: eth0
    ipam:
      config:
      - subnet: 10.1.1.0/24
        #ip_range: "10.1.1.221/30"
        #gateway: 10.1.1.1
  izpbx-1:
    driver: bridge

services:
  db:
    image: mariadb:10.5.9
    ## WARNING: if you upgrade image tag enter the container and run mysql_upgrade:
    ## source .env ; docker exec -it izpbx-db mysql_upgrade -u root -p$MYSQL_ROOT_PASSWORD
    command: --sql-mode=ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION
    restart: unless-stopped
    env_file:
    - .env
    environment:
    - MYSQL_ROOT_PASSWORD
    - MYSQL_DATABASE
    - MYSQL_USER
    - MYSQL_PASSWORD
    ## database configurations 
    volumes:
    - ./data/db:/var/lib/mysql
    networks:
      izpbx-1:

  izpbx:
    #hostname: ${APP_FQDN}
    image: izdock/izpbx-asterisk:18.15.11
    restart: unless-stopped
    depends_on:
    - db
    env_file:
    - .env
    volumes:
    - ./data/izpbx:/data
    cap_add:
    - SYS_ADMIN
    - NET_ADMIN
    privileged: true
    networks:
      izpbx-0-ext:
        ipv4_address: 10.1.1.221
      izpbx-1:
```

Repeat the procedure for every izPBX you want deploy. Remember to create a dedicated directory for every izpbx deploy.

#### Deploy
Enter in every directory containig configuration files and run:
- `docker-compose up -d`

### Multi-Tenant VoIP PBX with shared global Database and single docker-compose.yml file

#### Objective
- Run many izPBX instances into single docker host (you must allocate an external static IP for every izPBX backend/frontend)
- Single Global Shared Database used by all izPBX instances

#### Configuration
Create a directory where you want deploy all izpbx data and create `docker-compose.yml` and a `PBXNAME.env` file for every izpbx deploy:

Example:
```
mkdir izpbx
cd izpbx
vim docker-compose.yml
vim izpbx1.env
vim izpbx2.env
vim izpbx3.env
```
etc...

NOTE:
- Modify `docker-compose.yml` according to your environment needs, changing:
  - `parent:` (must be specified your ethernet card)
  - `subnet:` (must match you intranet network range)
  - `ipv4_address:` (every izPBX frontend will must to have a different external IP)
- Rembember to modify every `PBXNAME.env` file and set different variables for `MYSQL` (for best security use a different password for every deploy), example:
  - `MYSQL_SERVER=db` (all deployes will use the same db name)
  - `MYSQL_DATABASE=izpbx1_asterisk`
  - `MYSQL_DATABASE_CDR=izpbx1_asteriskcdrdb`
  - `MYSQL_USER=izpbx1_asterisk`
  - `MYSQL_PASSWORD=izpbx1_AsteriskPasswordV3ryS3cur3`
  - so on...

```yaml
version: '3'

networks:
  izpbx-0-ext:
    driver: macvlan
    driver_opts:
      parent: enp0s13f0u3u1u3
    ipam:
      config:
      - subnet: 10.1.1.0/24
  izpbx-1:
    driver: bridge

services:
  db:
    image: mariadb:10.5.9
    ## WARNING: if you upgrade image tag enter the container and run mysql_upgrade:
    ## source .env ; docker exec -it izpbx-db mysql_upgrade -u root -p$MYSQL_ROOT_PASSWORD
    command: --sql-mode=ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION
    restart: unless-stopped
    env_file:
    - db.env
    environment:
    - MYSQL_ROOT_PASSWORD
    - MYSQL_DATABASE
    - MYSQL_USER
    - MYSQL_PASSWORD
    ## database configurations 
    volumes:
    - ./data/db:/var/lib/mysql
    networks:
      izpbx-1:

  izpbx1:
    #hostname: ${APP_FQDN}
    image: izdock/izpbx-asterisk:18.15.11
    restart: unless-stopped
    depends_on:
    - db
    env_file:
    - izpbx1.env
    volumes:
    - ./data/izpbx1:/data
    cap_add:
    - NET_ADMIN
    privileged: true
    networks:
      izpbx-0-ext:
        ipv4_address: 10.1.1.221
      izpbx-1:

  izpbx2:
    #hostname: ${APP_FQDN}
    image: izdock/izpbx-asterisk:18.15.11
    restart: unless-stopped
    depends_on:
    - db
    env_file:
    - izpbx2.env
    volumes:
    - ./data/izpbx2:/data
    cap_add:
    - NET_ADMIN
    privileged: true
    networks:
      izpbx-0-ext:
        ipv4_address: 10.1.1.222
      izpbx-1:

  izpbx3:
    #hostname: ${APP_FQDN}
    image: izdock/izpbx-asterisk:18.15.11
    restart: unless-stopped
    depends_on:
    - db
    env_file:
    - izpbx3.env
    volumes:
    - ./data/izpbx3:/data
    cap_add:
    - NET_ADMIN
    privileged: true
    networks:
      izpbx-0-ext:
        ipv4_address: 10.1.1.223
      izpbx-1:
```

#### Deploy
Enter the directory containig configuration files and run:
- `docker-compose up -d`

# Services Management

### Command to restart whole izPBX deploy
`docker-compose restart izpbx`

### Command to restart izPBX container only
`docker restart izpbx`

### Command to restart DB container only
`docker restart izpbx-db`

### If you want restart single services inside `izpbx` container
Enter the container:  
`docker exec -it izpbx bash`

Restart izpbx service (Asterisk Engine):  
`supervisorctl restart izpbx`

To restart others available services use `supervisorctl restart SERVICE`

Available services:  
  - `asterisk`
  - `cron`
  - `fail2ban`
  - `fop2`
  - `httpd`
  - `izpbx`
  - `tftpd`
  - `postfix`
  - `zabbix-agent`

# Tested systems and host compatibility
Tested Docker Runtime:
  - moby-engine 19.03
  - docker-ce 19.03
  - docker-compose 1.25

Tested Host Operating Systems:
  - RHEL 6/7/8 based distro
  - Fedora Core >30
  - Debian 10
  - Ubuntu 20.04


# FreePBX Configuration Best Practices
* **Settings-->Advanced Settings**
  * CW Enabled by Default: **NO**
  * Country Indication Tones: **Italy**
  * Ringtime Default: **60 seconds**
  * Speaking Clock Time Format: **24H**
  * PHP Timezone: **Europe/Rome**
  
* **Settings-->Asterisk Logfile Settings**
  * Security Settings-->Allow Anonymous Inbound SIP Calls: **No**
  * Security Settings-->Allow SIP Guests: **No**

* **Settings-->Asterisk SIP Settings**
  * File Name: **security**
  * Security: **ON** (all others OFF)
  
* **Settings-->Filestore-->Local**
  * Path Name: **Local Storage**
  * Path: **__ASTSPOOLDIR__/backup**

* **Admin-->Backup & Restore**
  * Basic Information-->Backup Name: **Daily Backup**
  * Notifications-->Email Type: **Failure**
  * Storage-->Storage Location: **Local Storage**
  * Schedule and Maintinence-->Enabled: **Yes**
  * Schedule and Maintinence-->Scheduling: Every: **Day** Minute: **00** Hour: **00**
  * Maintinence-->Delete After Runs: **0**
  * Maintinence-->Delete After Days: **14**

* **Admin-->Contact Manager**
  * External
    * Add New Group
      * Name: **PhoneBook**
      * Type: **External**
  
* **Admin-->Caller ID Lookup Sources**
  * Source Description: **ContactManager**
  * Source type: **Contact Manager**
  * Cache Results: **No**
  * Contact Manager Group(s): **All selected**
  
* **Admin-->Sound Languages-->Setttings**
  * Global Language: **Italian**

# Configuring VoIP XML PhoneBook Lookup
NOTE: Tested on Yealink Phones

- Configure **Contact Manager** as reported above (the Contact Manager GroupName be MUST named **PhoneBook** otherwise doesn't works by default)

## Option 1: PhoneBook Menu
- Open VoIP Phone GUI (Yealink Phone GUI):
  - **Directory-->Remote Phone Book**
    - Index 1 (URL for XML Menu)
      - RemoteURL: **http://PBX_ADDRESS/pb**
      - Display Name: **PhoneBook**

## Option 2: Define every PhoneBook you want to use
- Open VoIP Phone GUI (Yealink Phone GUI):
  - **Directory-->Remote Phone Book**
    - Index 1 (URL for Extensions PhoneBook)
      - RemoteURL: **http://PBX_ADDRESS/pb/yealink/ext**
      - Display Name: **Extensions**
    - Index 2 (URL for Shared PhoneBook)
      - RemoteURL: **http://PBX_ADDRESS/pb/yealink/cm**
      - Display Name: **Shared Phone Book**
      
# FAQ / Troubleshooting
- FOP2 useful commands:
    NB. define interface name to associate the license, for example: `eth0`
    - enter into izpbx container: `docker exec -it izpbx bash`
    - register the license: `/usr/local/fop2/fop2_server --rp=http --register --iface eth0 --name "Company Name" --code "LICENSECODE"`
    - get lincese detail: `/usr/local/fop2/fop2_server --rp=http --getinfo --iface eth0`
    - reactivate the license: `/usr/local/fop2/fop2_server --rp=http --reactivate --iface eth0`
    - revoke the license: `/usr/local/fop2/fop2_server --rp=http --revoke --iface eth0`

- FOP2 is running in Demo mode because the license is invalid
  - FOP2 soffer from a bug about the lincensing model (already comunicated many times to the FOP2 support without an official solution)
    to workaround that problem, normally is required to **reactivate** the license, but some times doesn't works, so the only solution is to contact FOP2 support team

- FreePBX is slow to reload (https://issues.freepbx.org/browse/FREEPBX-20559)
  - As temporary WORKAROUND enter into izpbx container shell and run:  
    `docker exec -it izpbx bash`  
    `fwconsole setting SIGNATURECHECK 0`

- Factory Reset izPBX (WARNING! your persistent storage will be wiped!):
  - `docker-compose down`
  - `rm -rf data`
  - `docker-compose up -d`
