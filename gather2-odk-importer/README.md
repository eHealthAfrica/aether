# ODK Importer for Gather2

> Interface between Gather2 API and ODK Collect App

## Setup

## Setup


### Dependencies

git

[docker-compose](https://docs.docker.com/compose/)


### Installation


```sh
git clone git@github.com:eHealthAfrica/gather2.git
cd gather2

docker-compose up -d db 
docker-compose run importer startupimporter.sh setupdb
docker-compose up importer
```

go to localhost:7000 in the host browser, eh voila!
