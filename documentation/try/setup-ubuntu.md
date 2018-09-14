---
title: Ubuntu Setup for Aether and Gather
permalink: documentation/try/setup-ubuntu.html
description: Aether Documentation – Setting up Ubuntu for Aether and Gather evaluation
---
# Set up Ubuntu for evaluating Aether and Gather
This guide will take you through the steps required to get your Ubuntu system ready to evaluate and use Gather and Aether in a **Non Production** environment. This is the same configuration that our internal developers use. It uses Docker images to host the processes within a self contained virtual environment.  When that environment is deleted, all data will be lost.  

**System requirements:**
* 64-bit, Intel based computer with at least 8GB RAM
* Internet connection
* Ubuntu version 16.x or newer
* Both server and client browser are running on the same machine
* You are authorized and have the password to `sudo` as root

_These instructions have been tested with Version 16.04_

## Overview of the setup process
* Verify these ports are not in use: 80, 8000, 8443 and 5000
* [Git](https://git-scm.com/)  is installed 
* [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/) and [Docker Compose](https://docs.docker.com/compose/) are installed. It helps if Docker can be [run as a non-root user](https://docs.docker.com/install/linux/linux-postinstall/)

## Detailed Steps

In order to interact with the services via browser, the following ports must be available:
* 80 - for the Aether and Gather UI
* 8000 - for experimenting with the Aether REST API
* 8443 - for ODK Collect to connect to the server
* 5000 - for interacting with the CKAN Portal

[![Ubuntu Available Ports](/images/ubuntu-ports.png)](/images/ubuntu-ports.png){: .scalable}**Verify Available Ports -** At the shell command line, run the **lsof** command below and verify that the above ports are not in use.  The screenshot shows what an in use port looks like.  You must exit the process that is using any of the above ports.
<p style="clear: both;"/>
```
sudo lsof -nPiTCP -sTCP:LISTEN
```
[![Ubuntu Versions](/images/ubuntu-versions.png)](/images/ubuntu-versions.png){: .scalable}**Verify Docker, Docker Compose and Git versions -** These tools need to be installed in order to install and run the Gather and Aether services.  Execute the following commands, verify the versions and go to the corresponding section for install instructions.  

_**Docker version** 18.x or newer **Docker Compose** version 1.20.x or newer and **git** version 2.7.x or newer_

<p style="clear: both;"/>

```
docker --version

docker-compose --version

git --version
```
[![AWS EC2 APT Update](/images/aws-ec2-docker1.png)](/images/aws-ec2-docker1.png){: .scalable}**Install Docker Step 1 -** Update the _apt_ package index and verify that the necessary tools are installed on the system.  Add Docker’s official GPG key and setup the latest stable Docker repository. Finally, update the package index again for Docker. If you want more information about what you are installing, see the [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/) install pages on the Docker web site.
<p style="clear: both;"/>

```
sudo apt-get update

sudo apt-get install apt-transport-https ca-certificates curl software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

sudo apt-get update
```
<p style="clear: both;"/>

[![AWS EC2 Docker](/images/aws-ec2-docker2.png)](/images/aws-ec2-docker2.png){: .scalable}**Install Docker Step 2-** Execute the **apt-get** command below and answer **Y** when prompted to continue.  

By default, the docker install does not add any users to the docker group.  This requires you to prepend all docker commands with **sudo** in order to have permission to execute them.  You can optionally run the **usermod** command below to add the current user to the docker group and not have to use **sudo**. For more information about the security implications of this, see [Manage Docker as a non-root user](https://docs.docker.com/install/linux/linux-postinstall).
<p style="clear: both;"/>

```
sudo usermod -aG docker $USER
```
_After the usermod command, you will have to `exit` and then re-login to your instance._

[![AWS EC2 Docker Compose](/images/aws-ec2-docker3.png)](/images/aws-ec2-docker3.png){: .scalable}**Install Docker Compose -**  Get latest Docker Compose.  At the time of this writing, the latest version was 1.22.0.  Over time, you may want to [check the latest version](https://github.com/docker/compose/releases) and change **1.22.0** to that version.  After installing Docker Compose, verify that both it and Docker works.
<p style="clear: both;"/>

```
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

docker-compose --version

docker run hello-world
```

_If you had a permission error running Docker's "Hello World" then you didn't run the **usermod** statement from above or you didn't exit and log back in.  Otherwise, you will have to prepend **sudo** to all docker commands._

[![AWS EC2 Git](/images/ubuntu-git.png)](/images/ubuntu-git.png){: .scalable}**Install/Upgrade Git -** The latest version of git for Ubuntu is maintained by [these people](https://launchpad.net/~git-core/+archive/ubuntu/ppa).  The following commands will install/upgrade git to the latest stable version.  Answer **Y** when prompted to continue.
<p style="clear: both;"/>

```
sudo add-apt-repository ppa:git-core/ppa

sudo apt-get update

sudo apt-get install git
```

Congratulations!!! Your environment should now be set up to try Aether or Gather.

<div style="margin-top: 2rem; text-align: center"><a href="http://gather.ehealthafrica.org/documentation/try/setup">Continue to Gather Install</a><br/>
<a href="install">Continue to Aether Install</a></div>

