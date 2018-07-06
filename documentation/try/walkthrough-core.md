---
title: Aether - Setting Up an Aether-Based Solution
permalink: documentation/try/walkthrough-core.html
---

# A Simple Aether-Based Solution

We’re going to take raw JSON data that has been collected during a microcensus, and learn how to break that data into pieces that can then be sent to different destinations. In Aether we do this by creating a new _pipeline_. 

A pipeline consists of a path that data takes through Aether, and the transformations that it goes through along the way. Within a pipeline, we define one or more _data contracts_ that specify the format of the transformed data, along with rules that define how the input data is transformed to comply with those contracts.

These contracts are defined using _schemas_, and the transformed data is known as _entities_, for reasons that will, hopefully, soon become obvious.

In the `assets` folder of the `aether-bootstrap` repository contains some sample data, some schemas and a set of mappings. For the purposes of this walkthrough, we’re going to copy and paste the contents of these files into the Aether UI (for a more detailed overview of the UI, check out its [documentation](/documentation/ui/)).

Open the [UI](http://ui.aether.loca) and log in if you haven’t already. We’re going to create a new pipeline, so hit the button that’s handily labelled _NEW PIPELINE_. Enter a name, and press _START PIPELINE_.

## Defining Our Input

The first thing you see is the input screen, where you can either paste some raw JSON data, or an AVRO schema that defines your input data. Open the `sample-data.json` file from the `assets` folder, copy the contents, and paste it into the text area. It should now look like this:

![Input data](/images/walkthrough-1.png)

At the bottom of the screen is a button labelled _DERIVE DATA FROM SCHEMA_. Click this, and Aether will generate an AVRO schema for you. The structure of the sample data is now shown in the sidebar.

## Defining Our Output Contracts

Now we’re going to add some _entity type definitions_. These are (more) schemas that constitute the _data contracts_ we mentioned earlier. Click on _ENTITY TYPES_, open `all.json` in `assets/schemas` and copy and paste everything into the text area where it says _Enter your schemas_. Click _ADD TO PIPELINE_.

![Entity types](/images/walkthrough-2.png)

## Defining Our Mappings

The third and final step is to create the mapping rules that specify how the input data is transformed into entities. Normally you would probably add these mappings one by one using the interface provided by the UI, but for the purposes of this walkthrough we’re going to - you guessed it - copy and paste the mapping definition from the `assets` folder. 

Open up `mapping.json` from `assets/mappings/` and copy the contents. In the UI, click on _MAPPING_, and then go to the tab labelled _JSON_. Paste everything into the text area and click on _APPLY MAPPING RULES TO PIPELINE_.

![Mappings](/images/walkthrough-3.png)


Fields in the _INPUT_ and _ENTITY TYPES_ sidebars are now highlighted to indicate mappings between them; if you click on the _Mapping rules_ tab you can see the individual mapping rules.

You might also have noticed the green dot next to the _OUTPUT_ section in the top right hand corner of the screen. This indicates that your pipeline is successfully creating entities, i.e. that the data is being transformed and broken up into pieces as defined by our schemas. Open the _OUTPUT_ screen, and you’ll see the transformed data.

Congratulations! You have just completed the set-up of your first Aether-based solution.

The next step is to send the entities to CKAN and Elastic Search / Kibana.