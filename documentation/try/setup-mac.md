---
title: Mac Setup for Aether and Gather
permalink: documentation/try/setup-mac.html
description: Aether Documentation – Setting up Mac for Aether and Gather evaluation
---

# Set up Mac for evaluating Aether and Gather
This guide will take you through the steps required to get your Mac ready to evaluate and use Gather and Aether in a **Non Production** environment.  This is the same configuration that our internal developers use. It uses Docker images to host the processes within a self contained virtual environment.  When that environment is deleted, all data will be lost.  

**System requirements:**
* 64-bit, Intel based computer with at least 8GB RAM
* Internet connection
* OS X El Capitan 10.11 and newer macOS releases.
* Both server and client browser are running on the same machine
* You have Administrator and `sudo` privileges

_These instructions have been tested with macOS High Sierra 10.13_

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

[![Mac Available Ports](/images/mac-ports.png)](/images/mac-ports.png){: .scalable}**Verify Available Ports -** At the shell command line, run the **lsof** command below and verify that the above ports are not in use.  The screenshot shows what an in use port looks like.  Terminate the processes that are using any of the above ports.
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
[![Mac Docker](/images/mac-docker.png)](/images/mac-docker.png){: .scalable}**Install Docker and Docker Compose -** A graphical installer for Mac is available on the Docker website.  Please follow the [Get Docker Community Edition for Mac](https://store.docker.com/editions/community/docker-ce-desktop-mac) install instructions.  Docker Compose will also be installed with the installer.
<p style="clear: both;"/>

[![Mac Git](/images/mac-git.png)](/images/mac-git.png){: .scalable}**Install/Upgrade Git -** Git has a graphical installer for Mac available on their website.  Please download and follow [Installing on Mac](https://git-scm.com/download/mac)  instructions.  If you get the message that the install package is from an unknown developer, go to **System Preferences** and open the **Security & Privacy** app and press the **Open Anyway** button.
<p style="clear: both;"/>

Congratulations!!! Your environment should now be set up to try Aether or Gather.

<div style="margin-top: 2rem; text-align: center"><a href="http://gather.ehealthafrica.org/documentation/try/setup">Continue to Gather Install</a><br/>
<a href="install">Continue to Aether Install</a></div>

