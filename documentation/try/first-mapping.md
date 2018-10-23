---
title: Aether - A Simple Aether-Based Solution
permalink: documentation/try/first-mapping.html
description: Aether Documentation – Try It for yourself
---

# A Simple Aether-Based Solution

Aether is a platform for building solutions that curate and exchange live information. Structured data is "pushed" to Aether via client API.  The input data is combined with known schemas and _mapping functions_ resulting in the extraction of one or more _entity objects._

Entities are standalone data documents that each contain a matadata "contract" or schema.  The schema describes the structure of the data represented by the entity.  The entities (document/schema bundles) are passed along to a queing mechanism and made available to downstream data consumers.  

![Highlevel Flow](/images/highlevel-flow.png)

An example of this type of entity extraction is [normalizing](https://en.wikipedia.org/wiki/Database_normalization) an entry of data from a census form.  There may be information about the physical location, some household information, the names, ages and sex of people living in the houshold etc.  Using a mapping that you build, Aether's entity extractor could generate 3 kinds of entities from this row of data:  Location, Household and Person.  You also have the ability to give each entity a globally unique ID and link the entities together logically.  

In Aether speak, we call this process a **pipeline**.  A pipeline consists of a path that data takes through Aether, and the transformations that it goes through along the way. Within a pipeline, we define one or more _data contracts_ that specify the format of the transformed data, along with rules that define how the input data is transformed to comply with those contracts.

You should already be set up, logged in and looking at a mostly empty **Aether//Pipelines** screen from the [previous step](index)

![AUX](/images/screenshots/pipelines-overview-start.png)
{: .screenshot}

## Try it Yourself
In this exercise, we will setup a system for health facilities to report their current stock level of vaccines. Software at each facility will communicate to this reporting system by making REST calls. We don't worry about what the implementation at the facility will be, our job is to define the document structures, make REST endpoints available to accept those documents and handle the downstream data flow.

### Input
There are two types of information that the system will need to know about.  The registration information for a **new facility** and the actual **stock report** from an existing facility.  We start with facility registration using the document structure below, and define an Aether pipeline.

**A new facility registration document**
```json
{
  "name": "Berlin Office Clinic",
  "location": {
    "lat": 52.514590,
    "lng": 13.363895
  }
}
```
On the [Aether UI]([http://ui.aether.local), hit the button that’s labelled _NEW PIPELINE_ , create a new pipeline called `Clinic Registration` and press _START PIPELINE_.

In the input tab page, paste the sample data into the `JSON Data` section, and press `Derive Schema From Data`

![Input](/images/01-input.png)

_**So what just happened?**_
1. _We "told" the Aether Pipeline Editor that we do not have a schema for the incoming data but we do have a sample of the data._
2. _We asked Aether to generate a schema from the data._
3. _Aether showed us a graphical representation of the schema it generated._ 

### Output
We used a data sample to generate the schema used as the input contract for facility registration.  For the facility entity that we will send out, we will use an [AVRO Schema](https://en.wikipedia.org/wiki/Apache_Avro).  To keep this example simple, we will not add too much to the facility entity that will we will generate. We already have a name and a location for our clinic but to ensure consistancy, in case a clinic is renamed or the original data was incorrect, we should give it an ID and include a revision field as well. Taking that into account, we need a schema for `Health Facility` that looks like this:

```json
[
  {
    "doc": "Health Facility",
    "name": "Facility",
    "type": "record",
    "fields": [
      {
        "doc": "ID",
        "name": "id",
        "type": "string",
        "jsonldPredicate": "@id"
      },
      {
        "doc": "Revision",
        "name": "rev",
        "type": "string"
      },
      {
        "type": "string",
        "name": "name"
      },
      {
        "type": "float",
        "name": "lat"
      },
      {
        "type": "float",
        "name": "lng"
      }
    ],
    "namespace": "eha.demo"
  }
]
```
Click on step 2 `Entity Types`, paste the definition above and select `Add to Pipeline`.

![Input](/images/02-entities.png)

### Mapping
Now that we have an input defined and created a schema for our entity, we define our mapping functions. Click on step 3 `Mappings` to bring up the mapping UI. While building a mapping, it's helpful to see what the output of entity extraction will be in real time. Aether provides this feedback via the `Output` section. You can show or hide it at any time by pressing the arrow next to the `Output` label. Open it now.

![Input](/images/03-mapping.png)

The mapping is a set of instructions that transform our input in the something conforming to our entity schema. There are two parts to a mapping, a source and a destination. The source generally is the input, but sometimes we need to create or lookup data instead of just copying it. Looking at the input, there is no datum that fits our `id` field. In the case of IDs, we often want to create a new random ID and assign it. To do this we use an extractor function. You can identify these easily in mappings because they all start with the characters `#!`. We'll use `#!uuid` as our source, and assign it the destination path `Facility.id`. To do so, press `Add Rule`, fill in the values and then select `Apply Mapping Rules to Pipeline`.

![Input](/images/03a-mapping.png)

Once you do this, you'll notice a few things. In the Entities section, the `id` field is highlighted, because it has a mapping instruction associated with it. In the output section, we have a number of mapping errors. The validator is complaining because we have four fields that are required, for which we have no data. 

Let's fix that. First assign another UUID to Facility.rev as we did before. Next we want to assign values from the input for `name`, `lat` and `lng`. For the source, we'll use a jsonpath expression. For example, the correct path for the name field is `$.name`. For a nested field like lat, we need `$.location.lat`. Following this pattern, you should arrive at this:

![Input](/images/03b-mapping.png)

You can now save this pipeline which will give you a submission URL. Data sent to this url will undergo this transformation and be saved in Aether as the entity type Facility. This is a very straight-forward example. We've added a few fields and taken `lat` and `lng` from the nested `location` object. In the next example, we'll tackle a more complex example that creates many entities from a single input document.

<div style="margin-top: 2rem; text-align: center"><a href="walkthrough-core">Next Step: A More Complex Aether-Based Solution</a></div>
