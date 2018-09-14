---
title: Aether - Try It
permalink: documentation/try/index.html
description: Aether Documentation – Try It for yourself
---

# Try Aether For Yourself

Aether is a platform. This means that it doesn’t do much on its own: it only makes sense to use it in the context of creating a solution. For this initial run-through, we’re going to create a simple solution that takes data collected in a microcensus and feeds it out to dashboards. We’ll start with some raw json input data, and create some mappings to transform it into a more useable state. After that, we'll see how that data can then be fed through to CKAN by using Aether Connect. But first things first...

## Prerequisites
Since Aether is a development platform, these instructions assume that you are a Developer or DevOps type person with familiarity with the commandline, github and docker. There isn't any programming required but the instructions will be challenging if you are not used to scripts, config files, JSON and just generally performing system admin type tasks.  If this is not you, Gather may be more apropriate.
[You can try Gather here](https://gather.ehealthafrica.org/documentation/try/).

You will need a computer running Linux, macOS, a cloud based Linux VM (such as AWS) or Windows 10.  A minimum of 8GB of RAM is also required.  These instructions have been tested on Ubuntu 16.04.x, Mac 10.13.x and Windows 10 Pro (1607).

- GitHub
    - [git](https://git-scm.com/) must be installed and available
- Docker
    - [Docker Compose](https://docs.docker.com/compose/) installed setup with at least 3GB limit
- The following ports should be available on your machine:  
80, 8000, 8004, 8443, 5000

## Setup Help
If you are unsure what all of the above means, we have some detailed steps that you can follow to get your computer configured to run these demos.  You will need an Intel based 64-bit computer with at least 8GB RAM.

**[Macintosh Setup Help](setup-mac)** for OS X El Capitan 10.11 and newer macOS releases.

**[Windows Setup Help](setup-windows)** for Windows 10 and newer releases.

**[Linux Setup Help](setup-ubuntu)** for Ubuntu 16.04.x and newer releases.

**[Amazon Web Services](setup-aws)** is a great way to evaluate Aether without having to install anything on your own computer.  From start to finish, it only takes about an hour to spin up an EC2 instance, configure it and try the following exercises.  This link will take you to a set of instructions that will help you (even if you are a beginner) get started with AWS and configured to run Aether.  It costs about $3.00 to start up an AWS EC2 instance and run it for 12 hours.

<div style="margin-top: 2rem; text-align: center"><a href="install">Next Step: Install Aether</a></div>
