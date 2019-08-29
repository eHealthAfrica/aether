---
title: Aether Install
permalink: documentation/try/install.html
description: Aether Documentation – Install
---
# Installing Aether
Aether actually consists of several different servers and services that run in their own virtual network environment.  More specifically, it utilizes container-based virtualization, which allows multiple isolated systems, called containers, to run on a single host and access a single kernel.  The container we use is [Docker](https://www.docker.com/) and we use [Docker Compose](https://docs.docker.com/compose/) to define and script deployment configurations (this is known as “orchestration”).  In production, Aether is deployed and maintained using [Kubernetes](https://kubernetes.io/), a more robust system that takes advantage of this technology.   

Before following this run-through, make sure you have met the prerequisites defined in the [previous section](index).
## Local Browser Client
As mentioned earlier, we are actually setting up an Aether development environment for these exercises.  In this environment, we need to define some domain names that will resolve to the actual location of the server.  It only needs to be done on the machine that you will be using your web browser from.  You will need to edit your **/etc/hosts** file which will require **Administrator** or **root** permissions.  Using your favorite plain text editor, open **/etc/hosts** for editing.  

If you are running both the Aether server and web browser client on the same computer, modify the line that starts with **127.0.0.1** as shown Below
```
127.0.0.1    localhost ui.aether.local kernel.aether.local
```
If your server is running remotely from your web browser, for example on AWS,  add a line to your **/etc/hosts** substsituting the IP address of your Aether server for **XX.XX.XX.XX**.  The new line should look like:
```
XX.XX.XX.XX  ui.aether.local kernel.aether.local
```

_NOTE: Editing your **/etc/hosts** file will **not** be required in a production environment._

## Into the Aether
We’ve created an **aether-bootstrap** repository to make it easy for you to get up and running with your first Aether-based solution. It contains a series of **docker-compose** files and shell scripts that will pull Docker images of the latest version of Aether from Docker Hub and start them up. 

_**If you have already tried the Gather demo, and that environement is still available, you don't need to clone the "aether-bootstrap" repository.  The "aether-bootstrap" folder can be found in the "gather-deploy" repository.**_

```
git clone https://github.com/eHealthAfrica/aether-bootstrap.git

cd aether-bootstrap
```
This demo is specific to version 1.4, A new 1.5 demo will be coming soon...

```
git fetch && git fetch --tags
git checkout 1.4.0
```

If you are starting Aether or Gather for the first time, you will need to create some docker resources (networks and volumes) and generate credentials for all applications:

```
./scripts/initialise_docker_environment.sh
```

Now you just need to tell Docker to download the images and start them up:

```
docker-compose up
```

Once the console output has stopped, you should be able to access the Aether UI in your browser at [http://ui.aether.local/](http://ui.aether.local/). Use these credentials to log in:

- _Username:_ **admin**
- _Password:_ **adminadmin**

If you see this screen, you are all configured and ready to move on:

![AUX](/images/screenshots/pipelines-overview-start.png)
{: .screenshot}

Now let’s [start creating our first Aether-based solution](first-mapping).

