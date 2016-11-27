# ODK Importer for Gather2

> Interface between Gather2 API and ODK Collect App

## Setup

## Setup


### Dependencies

git

[docker-compose](https://docs.docker.com/compose/)


### Installation


```
$ git clone git@github.com:eHealthAfrica/gather2.git
$ cd gather2/gather2_odk_importer

$ docker-compose up -d db 
$ docker-compose run startupimporter.sh setupdb
$ docker-compose up web
```

