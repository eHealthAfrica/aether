---
title: Aether - Try It - Aether Connect
permalink: documentation/try/walkthrough-connect.html
description: Aether Documentation – Try It for yourself
---

# Adding Aether Connect

So far we have set up mappings so that we can be sure that our data conforms to predefined contracts. We used schemas to specify these contracts, and then saw how the data was transformed into entities based on those schemas.

We’re now going to find out how we can get this mapped data to be published in real time. This is done by **Aether Connect**, which is a system that uses Kafka plus pluggable "consumers" in order to stream entities out to various destinations. Right now we have a consumer for [CKAN](https://github.com/eHealthAfrica/aether-ckan-consumer) and an [SDK](https://github.com/eHealthAfrica/aether-consumer-sdk) to enable anyone to develop their own.

Bringing up Aether Connect is just a question of enabling it on the relevant file `options.txt`:

```text
## Kafka
ENABLE_CONNECT=true
AETHER_CONNECT_MODE=LOCAL
```

Then

You can check that this worked by opening <http://aether.local/dev/producer/check-app> in your browser. You should see something like this:

```json
{
    "app_name": "aether-producer",
    "app_version": "2.2.10",
    "app_revision": "608273ddf24124437deee1d5627a2ad015546b0b",
    "now": "..."
}
```

Also opening <http://aether.local/dev/producer/check-app/aether-kernel> or <http://aether.local/dev/producer/check-app/kafka> in your browser.

You should see something like this:

```json
{
    "healthy": true
}
```

This is the health check pages for the Aether Producer, which sits between the Aether Kernel and Kafka, passing out entities as they are created. We can see that both `kafka` and `aether-kernel` have `healthy` set to `true`. This means that the Aether Producer has successfully communicated with both of them.

To check the current topics open <http://aether.local/dev/producer/topics> with the producer credential included in `.env` file.

We can also see that four topics have been created, `Survey`, `Building`, `Household` and `Person`. Kafka separates its data feeds into separate topics, and the Producer automatically creates a new topic for each schema in Kernel. The Producer has found the entities that were created when we submitted data using `curl`, and has passed them to Kafka.

So now that we have got some entities _into_ Kafka, how do we get them out? That’s where we need a consumer. We’re going to use the CKAN consumer, so that we can watch our data get published to CKAN in real time. Starting the CKAN Consumer is pretty easy (clue: it rhymes with “flocker plompose”), but before we can do that we’ll need to take a short diversion so that we can get CKAN up and running.

## Installing CKAN

We've included `docker-compose` configurations for both the CKAN Consumer and itself CKAN in the aether-bootstrap repository for easy installation. As with Aether, the images you need will be pulled from dockerhub. From the aether-bootstrap base folder, we'll start by setting up CKAN.

Bringing up CKAN is just a question of enabling it on the relevant file `options.txt`:

```text
## CKAN
ENABLE_CKAN=true
```

Then

```bash
scripts/start.sh
```

Now go to <http://localhost:5000/organization> and add a new organization:

![Adding an Organization in CKAN](/images/ckan-organizations.png)

Name it `eHADemo` and click **Create Organization**.

Now that we have CKAN running, we need to turn to Aether Connect, the data publishing half of the Aether platform.

## Setting Up the CKAN Consumer

In order to communicate with CKAN, the CKAN Consumer needs an API Key. This can be found in the CKAN User page at <http://localhost:5000/user/admin>:

![Getting the CKAN API Key](/images/ckan-api-key.png)

If it's not present you can regenerate it in this page <http://localhost:5000/user/edit/admin>, clicking on **Regenerate API Key**.

![Getting the CKAN API Key](/images/ckan-regenerate-api-key.png)

Now you need to set up it in the CKAN Consumer.  Using the consumer API usually on <http://aether.local/dev/ckan-consumer>, register the following artifact.

POST <http://aether.local/dev/ckan-consumer/add>

```json
  {
    "id": "ckan-id",
    "name": "CKAN Instance",
    "url": "http://ckan:5000",
    "key": "[your-ckan-api-key]"
  }
```

## Submit Some More Data

If you want to see how data is published to CKAN in real time, you can re-submit the data via curl:

```bash
curl -H "Content-Type: application/json" \
    --data @assets/resources/submission.json \
    http://admin:adminadmin@aether.local/dev/kernel/submissions/
```

## Create a view in CKAN

If you now load the datasets page for our organization and see the various types of entities: <http://localhost:5000/dataset>. We're going to create a map of the [Buildings](http://localhost:5000/dataset/building) which have been submitted.

- Select Building from the Dataset screen. You should see metadata about the Dataset.
- Under **Data and Resources** click on the resource titled "Building". You should see a data dictionary for the resource.
- At the top of the page, press the button titled _Manage_ with a wrench icon. This will open a tabbed page about the resource.
- Select the tab titled _Views_.
- Press the button titled _+ New View_ and select _Data Explorer_ from the dropdown.
- Give the view a title like "My View" and select **Add** at the bottom of the page.
- From the menu of views, select the view you just created. At the bottom of the page, you should see a "View Preview"
- Above the data, there are view types like **Grid** and **Graph**. Select **Map**.
- In the menu to the right of the map, select the Latitude and Longitude fields and press **Update**.
- Enjoy your map!

## Recap

- we learned about Aether Connect, and how it consists of the Aether Producer, Kafka and Aether Consumers
- we started Aether Connect and saw the Producer’s status page
- we set up a local instance of CKAN
- we ran the Aether CKAN Consumer, learned a little about how it’s configured, and saw how it feeds data to CKAN
