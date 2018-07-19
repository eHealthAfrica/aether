---
title: Aether - Try It
permalink: documentation/try/index.html
---

# Try Aether For Yourself

Aether is a platform. This means that it doesn’t do much on its own: it only makes sense to use it in the context of creating a solution. For this initial run-through, we’re going to create a simple solution that takes data collected in a microcensus and feeds it out to dashboards. We’ll start with some raw json input data, and create some mappings to transform it into a more useable state. 

In the next step, we'll see how that data can then be fed through to Elastic Search by using Aether Connect, but first things first...

We’ve created an `aether-bootstrap` repository to make it easy for you to get up and running with your first Aether-based solution. This contains a bunch of `docker-compose` files that will pull Docker images of the latest version of Aether from Docker Hub and start them up. 

## Prerequisites

In order to follow this run-through, you will need to have [Docker](https://www.docker.com) installed (version 2.1 or higher).

You will also need to register some domains for local resolution on your computer. This means editing your hosts file. On Mac/Linux this is at `/etc/hosts`; on Windows it’s at `c:\Windows\System32\Drivers\etc\hosts`. Add this line to the bottom:

```
127.0.0.1       ui.aether.local kernel.aether.local
```

## Into the Aether

The easiest way to start building an Aether-based solution is to use _Aether Bootstrap_. Begin by cloning this repository to your computer:

```
git clone git@github.com:eHealthAfrica/aether-bootstrap.git
cd aether-bootstrap
```

Now you just need to tell Docker to download the images and start them up:

```
docker-compose up
```

Once the console output has stopped, you should be able to access the Aether UI in your browser. Use these credentials to log in:

- _Username:_ **admin**
- _Password:_ **adminadmin**

Now let’s [start creating our first Aether-based solution](walkthrough-core).


