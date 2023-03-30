---
title: Aether Install
permalink: documentation/try/install.html
description: Aether Documentation – Install
---

# Installing Aether

Aether actually consists of several different servers and services that run in their own virtual network environment.  More specifically, it utilizes container-based virtualization, which allows multiple isolated systems, called containers, to run on a single host and access a single kernel.  The container we use is [Docker](https://www.docker.com/) and we use [Docker Compose](https://docs.docker.com/compose/) to define and script deployment configurations (this is known as “orchestration”).  In production, Aether is deployed and maintained using [Kubernetes](https://kubernetes.io/), a more robust system that takes advantage of this technology.

Before following this run-through, make sure you have met the prerequisites defined in the [previous section](index).

## Local Browser Client

As mentioned earlier, we are actually setting up an Aether development environment for these exercises.  In this environment, we need to define some domain names that will resolve to the actual location of the server.  It only needs to be done on the machine that you will be using your web browser from.  You will need to edit your **/etc/hosts** file which will require **Administrator** or **root** permissions.  Using your favorite plain text editor, open **/etc/hosts** or **C:\Windows\System32\Drivers\etc\hosts** for editing.

If you are running both the Aether server and web browser client on the same computer, add a new line as shown below:

```text
127.0.0.1    aether.local
```

If your server is running remotely from your web browser, for example on AWS,  add a line to your **/etc/hosts** substituting the IP address of your Aether server for **XX.XX.XX.XX**.  The new line should look like:

```text
XX.XX.XX.XX  aether.local
```

_NOTE: Editing your **/etc/hosts** or **C:\Windows\System32\Drivers\etc\hosts** file will **not** be required in a production environment._

## Into the Aether

We’ve created an **aether-bootstrap** repository to make it easy for you to get up and running with your first Aether-based solution. It contains a series of **docker-compose** files and shell scripts that will pull Docker images of the latest version of Aether from Docker Hub and start them up.

```bash
git clone https://github.com/eHealthAfrica/aether-bootstrap.git

cd aether-bootstrap
```

If you are starting Aether or Gather for the first time, you will need to create some docker resources (networks and volumes), generate credentials for all applications and download the docker images:

```bash
./scripts/init.sh
```

_Note: Aether-Bootstrap enables multitenancy! The default setup creates three tenants: dev, prod and test._

Now you just need to tell Docker to start them up:

```bash
./scripts/start.sh
```

Once the console output has stopped, you should be able to access the Aether UI in your browser at <http://aether.local/dev/>. Use these credentials to log in:

- _Username:_ **user**
- _Password:_ **password**

Then click on **ae**ther box, this will redirect to: <http://aether.local/dev//kernel-ui/>

If you see this screen, you are all configured and ready to move on:

![AUX](/images/screenshots/pipelines-overview-start.png)
{: .screenshot}

Now let’s [start creating our first Aether-based solution](first-mapping).
