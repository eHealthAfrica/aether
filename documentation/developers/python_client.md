## Using the Aether Kernel's Python Client.

Since aether-kernel uses OpenAPI to describe it's interfaces, we can use a number of generic clients to communicate with it. When running locally, you can view the OpenAPI (formerly called Swagger) specification at [http://kernel.aether.local/v1/swagger/](http://kernel.aether.local/v1/swagger/). This is a good place to familiarize yourself with the API, and a good reference when you run into issues using the client. The client itself really only knows what's in the spec, and applies a light wrapper around the OpenAPI client library [bravado](https://bravado.readthedocs.io/en/stable/).

Bravado provides us with models and methods that we can use to interact with the API. If you want to follow along, you'll need a python environment into which you've installed `aether.client` and a local instance of Aether Kernel. I suggest grabbing [aether-bootstrap](https://github.com/eHealthAfrica/aether-bootstrap). If you do, you can find a copy of `aether.client` in the folder `aether-bootstrap/assets/generation/pip/requires`. This guide refers to v 0.10 and above. I also highly recommend you use [pipenv](https://pipenv.readthedocs.io/en/latest/) to isolate your python workspaces.



Connecting to the API is simple.
```python

from aether.client import Client

URL = 'http://kernel.aether.local'  # or the value of KERNEL_URL in the .env file
USER = 'admin'                      # or the value of KERNEL_USERNAME in the .env file
PW = 'adminadmin'                   # or the value of KERNEL_USERNAME in the .env file
client = Client(URL, USER, PW)
```

If we want to create project, we can get a model for it, and then populate it with our data and submit it to the kernel. You'll want to look at the Swagger spec hosted by [kernel](http://kernel.aether.local/v1/swagger/) to see what the required fields are for a given API call. In the case of a project, specifically the API method `projects_create`, it's just a name.

```python
Project = client.get_model('Project')  # get a copy of the model
my_project =  Project(name='my_project')  # only one field, name is required
# the naming convention for API calls goes, type -> function. 
# so the method project_create becomes => client.projects.create
created_project = client.projects.create(data=my_project)
# the returned project object will have information from the kernel for generated fields like ID, etc.
```

Creating Aether artifacts by hand is a pain, and I don't suggest you use the client API manual work. There are dependencies between schemas, project schemas, mappings, mappingsets that you shouldn't worry about if you don't have to. The Aether UI is better for such work. However, for querying and consuming entities, the API and it's client are great!

Let's say you registered the following pipeline through the AUX interface.

Input

```json
{
  "adults": [
    {
      "name": "Buster"
    },
    {
      "name": "Grace"
    }
  ],
  "address": "1000 Chortle Way",
  "children": [
    {
      "name": "Ace"
    },
    {
      "name": "Franklin"
    }
  ],
  "family_name": "Keaton"
}
```

Schemas

```json
[
  {
    "name": "FamilyMember",
    "type": "record",
    "fields": [
      {
        "name": "id",
        "type": "string",
        "jsonldPredicate": "@id"
      },
      {
        "name": "name",
        "type": "string"
      },
      {
        "name": "last_name",
        "type": [
          "null",
          "string"
        ]
      },
      {
        "name": "house",
        "type": "string",
        "jsonldPredicate": {
          "_id": "eha.aether.jokes.Home",
          "_type": "@id"
        }
      }
    ],
    "namespace": "eha.aether.jokes"
  },
  {
    "name": "Home",
    "type": "record",
    "fields": [
      {
        "name": "id",
        "type": "string",
        "jsonldPredicate": "@id"
      },
      {
        "name": "address",
        "type": "string"
      }
    ],
    "namespace": "eha.aether.jokes"
  }
]
```
Mapping

```json
[
  [
    "#!entity-reference#$.Home[*].id",
    "FamilyMember.house"
  ],
  [
    "$.family_name",
    "FamilyMember.last_name"
  ],
  [
    "$.adults[*].name",
    "FamilyMember.name"
  ],
  [
    "$.children[*].name",
    "FamilyMember.name"
  ],
  [
    "$.address",
    "Home.address"
  ],
  [
    "#!uuid",
    "FamilyMember.id"
  ],
  [
    "#!uuid",
    "Home.id"
  ]
]
```

Publishing that pipeline will register all those artifacts, as well as giving you the ID of the mapping set, let's call it `mappingset_id`.

Now let's say you want to push more data at that endpoint so that entities are extracted; how would that look?

```python
mappingset_id = 'the_id_that_AUX_gave_us'
payload = {  # This data matches our expected input schema.
  "adults": [
    {
      "name": "Frank"
    },
    {
      "name": "June"
    }
  ],
  "address": "101 Dalmation St.",
  "children": [
    {
      "name": "Jim"
    },
    {
      "name": "Alice"
    }
  ],
  "family_name": "Vandalay"
}

# get a Submission model.
Submission = client.get_model('Submission')
# taking a look at the swagger spec, submissions_create only requires payload and mappingset... so
my_submission = Submission(mappingset=mappingset_id, payload=payload)
response = client.submissions.create(data=my_submission)
```

To get an iterator that understands how Kernel pagaintes results, we use a special method called `paginated`. It can convert the result of any paginated output from an API call into a continuous, lazily evaluated iterator.

You still need to tell it which API method to call. For example, if you want to get the results of `submissions_list` you would use `client.submissions.paginated('list')` as follows:

```python

all_submissions = client.submissions.paginated('list')
for sub in all_submissions:
    print(sub)

```

To view all registered entities, we can use the same call on the entities endpoint.

```python

all_entities = client.entities.paginated('list')
for ent in all_entities:
    print(ent)

```

What if we want to filter based on the contents of the payload? Aether uses the [Django convention for object filtering](https://docs.djangoproject.com/en/2.1/topics/db/queries/#retrieving-specific-objects-with-filters). Let's say that we want to find "Frank Vandalay". We want to inspect `payload.name` and `payload.lastname` and we know the entity type is `FamilyMember`. Since we need an object in payload, we have to use the Django ORM syntax, so payload.name becomes `payload__name`. That's 2 underscore `_` characters replacing the typical path `.`.

```python
frank_entities = client.entities.paginated('list', payload__name="Frank")
for ent in frank_entities:
    print(ent)

```

It's also possible to extend this with functions supported by the Django ORM, like:
 - less than | `lt`
 - less than or equals | `lte`
 - starts with | `startswith`
 - etc ...

You can find a full listing in the [Django Object filtering docs](https://docs.djangoproject.com/en/2.1/topics/db/queries/#retrieving-specific-objects-with-filters). But using a similar example. we can do:

```python
e_entities = client.entities.paginated('list', payload__name__endswith="e")
for ent in e_entities:
    print(ent)

```


