---
title: Aether - Try It - Aether Connect
permalink: documentation/try/walkthrough-connect.html
description: Aether Documentation – Try It for yourself
---

# Adding Aether Connect

So far we have set up mappings so that we can be sure that our data conforms to predefined contracts. We used schemas to specify these contracts, and then saw how the data was transformed into entities based on those schemas. 

We’re now going to find out how we can get this mapped data to be published in real time. This is done by **Aether Connect**, which is a system that uses Kafka plus pluggable "consumers" in order to stream entities out to various destinations. Right now we have a consumer for [CKAN](https://github.com/eHealthAfrica/aether-ckan-consumer) and an [SDK](https://github.com/eHealthAfrica/aether-consumer-sdk) to enable anyone to develop their own.

Bringing up Aether Connect is just a question of running `docker-compose up` on the relevant file:

`docker-compose -f docker-compose-connect.yml up`

You can check that this worked by opening [http://localhost:5005/status](http://localhost:5005/status) in your browser. You should see something like this:

```
{
    kafka: true,
    kernel: true,
    topics: { ...
}
```

This is the status page for the Aether Producer, which sits between the Aether Kernel and Kafka, passing out entities as they are created. We can see that both `kafka` and `kernel` are set to `true`. This means that the Aether Producer has successfully communicated with both of them. 

We can also see that four topics have been created, `Survey`, `Building`, `Household` and `Person`. Kafka separates its data feeds into separate topics, and the Producer automatically creates a new topic for each schema in Kernel. The Producer has found the entities that were created when we submitted data using `curl`, and has passed them to Kafka.

So now that we have got some entities _into_ Kafka, how do we get them out? That’s where we need a consumer. We’re going to use the CKAN consumer, so that we can watch our data get published to CKAN in real time. Starting the CKAN Consumer is pretty easy (clue: it rhymes with “flocker plompose”), but before we can do that we’ll need to take a short diversion so that we can get CKAN up and running.

## Installing CKAN

We've included `docker-compose` configurations for both the CKAN Consumer and itself CKAN in the aether-bootstrap repository for easy installation. As with Aether, the images you need will be pulled from dockerhub. From the aether-bootstrap base folder, we'll start by installing CKAN.
```
scripts/setup_ckan.sh
```
This script will prompt you to create a user named `admin`, enter an email address and ask you for a password. Don’t forget the password that you enter; you will need it shortly. The email address can be any correctly formatted address but doesn't have to be a real one.

At the end of the process the script will output registration information, including an API key. 
```
Creating user: 'admin'
{'about': None,
 'activity_streams_email_notifications': False,
 'apikey': u'586c0901-65a6-4547-a80a-97438bcb9dd4',
  ...
}
```
Copy and save the API key. *Its the part between the single quotes*

Open `ckan-consumer/config/config.json` in your favourite editor, and change the value of `API_KEY` to what you just copied.

Now you can open CKAN in your browser - go to [http://localhost:5000](http://localhost:5000). Login using the password that you just entered. Select _Organizations_ from the top bar and create an organization with the name `eHADemo`.

## Start the CKAN Consumer and Do Some More CKAN Configuration

To start the CKAN Consumer:

```
docker-compose -f ckan-consumer/docker-compose.yml up
```

The `docker-compose.yml` file mounts an example configuration that we’ve included in this example, so feel free to take a look at it in `ckan-consumer/config/config.json`. Note that we’re telling the consumer which Kafka topics we’re interested in, and that we reference the organization that we set up in CKAN a moment ago.

## Submit Some More Data

If you want to see how data is published to CKAN in real time, you can re-submit the data via curl:

```
cd ../aether-bootstrap
curl -H "Content-Type: application/json" --data @assets/submission.json http://admin:adminadmin@kernel.aether.local/submissions/
```

## Create a view in CKAN

If you now load the datasets page for our organization and see the various types of entities: [http://localhost:5000/dataset](http://localhost:5000/dataset). We're going to create a map of the [Buildings](http://localhost:5000/dataset/building) which have been submitted.
  - Select Building from the Dataset screen. You should see metadata about the Dataset.
  - Under __Data and Resources__ click on the resource titled "Building". You should see a data dictionary for the resource.
  - At the top of the page, press the button titled _Manage_ with a wrench icon. This will open a tabbed page about the resource.
  - Select the tab titled _Views_.
  - Press the button titled _+ New View_ and select _Data Explorer_ from the dropdown.
  - Give the view a title like "My View" and select __Add__ at the bottom of the page.
  - From the menu of views, select the view you just created. At the bottom of the page, you should see a "View Preview"
  - Above the data, there are view types like __Grid__ and __Graph__. Select __Map__.
  - In the menu to the right of the map, select the Latitude and Longitude fields and press __Update__.
  - Enjoy your map!

## Recap

- we learned about Aether Connect, and how it consists of the Aether Producer, Kafka and Aether Consumers
- we started Aether Connect and saw the Producer’s status page
- we set up a local instance of CKAN
- we ran the Aether CKAN Consumer, learned a little about how it’s configured, and saw how it feeds data to CKAN

