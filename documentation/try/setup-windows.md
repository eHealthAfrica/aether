---
title: Windows Setup for Aether and Gather
permalink: documentation/try/setup-windows.html
description: Aether Documentation – Setting up Windows for Aether and Gather evaluation
---
# Set up Windows for evaluating Aether and Gather
This guide will take you through the steps required to get your Windows based computer ready to evaluate and use Aether and Gather in a **Non Production** environment.  This is the same configuration that our internal developers use.  It uses Docker images to host the processes within a self contained virtual environment.  When that environment is deleted, all data will be lost.  

**System requirements:**
* 64-bit, Intel based computer with at least 8GB RAM
* Internet connection
* Windows 10 Pro, Enterprise and Education (1607 Anniversary Update, Build 14393 or later).
* Both server and client browser are running on the same machine
* You have Administrator privileges

_These instructions have been tested with Windows 10 Pro (1607)_

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

[![Windows Available Ports](/images/windows-ports.png)](/images/windows-ports.png){: .scalable}**Verify Available Ports -** Open the Command Prompt in Administrator mode, right-click and choose **Run as administrator**.  Run the **netstat** command below and verify that the above ports are not in use.  The screenshot shows what an in use port looks like.  Terminate any processes using any of the above ports.  Use the **Process ID (PID)** along with **Task Manager** to find out what application is using the port.
<p style="clear: both;"/>
```
netstat -aon
``` 

[![Ubuntu Versions](/images/ubuntu-versions.png)](/images/ubuntu-versions.png){: .scalable}**Verify Docker, Docker Compose and Git versions -** These tools need to be installed in order to install and run the Gather and Aether services.  Execute the following commands, verify the versions and go to the corresponding section for install instructions.  

_**Docker version** 18.x or newer **Docker Compose** version 1.20.x or newer and **git** version 2.7.x or newer_

<p style="clear: both;"/>

```
docker --version

docker-compose --version

git --version
```
[![Windows Docker](/images/windows-docker.png)](/images/windows-docker.png){: .scalable}**Install Docker and Docker Compose -** A graphical installer for Windows is available on the Docker website. Please follow the [Install Docker for Windows](https://docs.docker.com/docker-for-windows/install/) instructions.  Docker Compose will also be installed with the installer.  On the **Daemon** tab in Docker preferences, make sure that the **Experimental features** box is **not** checked.
<p style="clear: both;"/>

[![Windows Git](/images/windows-git.png)](/images/windows-git.png){: .scalable}**Install/Upgrade Git -** Git has a graphical installer for Windows available on their website.  Please download and follow the [Installing on Windows](https://git-scm.com/download/win) instructions. 

<p style="clear: both;"/>

Congratulations!!! Your environment should now be set up to try Aether or Gather.

<div style="margin-top: 2rem; text-align: center"><a href="http://gather.ehealthafrica.org/documentation/try/install">Continue to Gather Install</a><br/>
<a href="install">Continue to Aether Install</a></div>

