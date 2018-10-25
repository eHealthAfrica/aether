## Mappings Functions and JSONPath Guide

A mapping is a set of instructions that when executed transform a source document into one or more entities. We call this process "entity extraction", and it's how Aether turns submissions into normalized entities.

Each mapping is made up of two instuctions, the first describing a source and the second a destination. The destination instruction will always be a reference to one of the entities we're trying to create. The source instruction can pull data from a few places, the most typical will be the source document. However, we can also use it to pull data from entities that have been created previously in the mapping, or to generate a new UUID, or to apply a constant not found found in the source document.

Mapping instructions are executed in order. To see how we handle missing references and other issues, see the section, [_Extractor Mechanism_](#user-content-extractor-mechanism).

#### Types of Mapping

There are two general types of instructions: JSONPath and it's extensions, and Extractor Functions. 
##### [_JSONPath Functions_](#user-content-jsonpath-function)
Look something like this: `$.path.to.somewhere[*].attribue`
##### [_Extractor Functions_](#user-content-extractor-function) 
Look something like this: `#!uuid` or `#!constant#male#string`

Let's construct an example that we can use to illustrates our mappings. We want to normalize this into two linked types. A Stooge who lives in a house, and a House with an address. We have a form with contact information that arrives in the following (pretty horrible) format:

<details open>
    <summary><i>Input <b>(Hide/Show)</b></i></summary>

```json
{
    "households": [
        {
        "names": [
            "Larry",
            "Curly"
        ],
        "address": "74 Whyioughta St.",
        "number1": 1,
        "number2": 2
        },
        {
        "names": [
            "Moe"
        ],
        "address": "1600 Ipoke Ave",
        "number1": 3
        }
    ]
}

```
</details>

<details open>
    <summary><i>Schema <b>(Hide/Show)</b></i></summary><br>

```json
[{
        "name": "Stooge",
        "type": "record",
        "fields": [{
                "name": "id",
                "type": "string",
                "jsonldPredicate": "@id"
            },
            {
                "name": "name",
                "type": "string"
            },
            {
                "name": "number",
                "type": "int"
            },
            {
                "name": "house",
                "type": "string",
                "jsonldPredicate": {
                    "_id": "eha.aether.jokes.House",
                    "_type": "@id"
                }
            }
        ],
        "namespace": "eha.aether.jokes"
    },
    {
        "name": "House",
        "type": "record",
        "fields": [{
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

</details>

<a name="jsonpath-function"></a>
## JSONPath Functions

JSONPath functions are based on the [jsonpath-ng](https://github.com/h2non/jsonpath-ng) implementation of the [JSONPath](https://goessner.net/articles/JsonPath/) specification. It's advisable to review both sets of documentation before continuing. JSONPath instructions are used to specify a location in the Source. It's conventional to start a JSONPath with the character `$`. We use a similar syntax for the destination, but we do not support the full syntax for reasons we'll discuss in a minute.

---
#### Simple JSONPath based copy operations

A simple case would be to copy the `address` from the source document and put it into a House entity under the property `address`.
```
src:    $.households[*].address 
dst:    House.address
```

As you can see, the Destination instruction `House.address` looks like a JSONPath. However, a sample output of the above instruction would be:

```json
[
    {"address" : "74 Whyioughta St."},
    {"address" : "1600 Ipoke Ave"}
]
```
`House` specifies the type of the object and tells Aether how to validate and where to save the data. It's not, strictly speaking, part of a valid JSONPath. This is why we don't use the `$` convention for Destination paths.

Similarly, we can resolve the names of our Stooges.

```
src:    $.households[*].names[*]
dst:    Person.name
```

This yields the expected:

```json
[
    {"name" : "Larry"},
    {"name" : "Curly"},
    {"name" : "Moe"}
]
```

---
#### JSONPath extensions

One annoying antipattern shows up in our sample input, the use of numbered keys like `number1` `number2` related keys in an object. JSONPath natively has no answer for this using the typical wildcard `*` operator. We've gone beyond the specification to enable the handling though. For example:

```
src:    $.households[*].number* 
dst:    Person.name
```
We would expect this to yield:

```json
[
    {"name" : "Larry", "number": 1},
    {"name" : "Curly", "number": 2},
    {"name" : "Moe", "number": 3}
]
```

---
#### JSONPath filtering and other functions

As we use the extended parser in `jsonpath-ng` there are a number of functional improvements that you can leverage. A reference is available [here](https://github.com/h2non/jsonpath-ng#extensions).

Filtering is an advanced feature and can change the order of the filtered field in the output entities. If you're creating more than one entity of a particular type, you must be sure that your outputs properly align to the source document as you're creating your mapping. The best way to do this is to:
  - Apply non-overlapping filtering to all instances of any filtered type.
  - Always apply filters in the same order.
  - Apply the same filter for all properties of a given type.

For more information about how the extractor interprets instructions, and why filtering order matters see the section titled [_Extractor Mechanism_](#user-content-extractor-mechanism).

<a name="extractor-function"></a>
## Extractor Functions

##### UUID
- *call:* `#!uuid`
- *args:* `none`
- *explanation:*

    Generates a random UUID (version 4) which can be assigned as a string to a field. Beyond generating the ID, this is saved as part of the original submission document in a section titled `aether_extractor_enrichment` so that if extraction is performed a second time against the same dataset, the same IDs will be used. This expects that the order of the entities within a type will not change. See [_Extractor Mechanism_](#user-content-extractor-mechanism) for more information on instruction ordering.

- *example:* 
```json
    ["#!uuid", "Person.id"]
```
---

##### Constant
- *call:* `#!constant`
- *args:*
    - 1: the value of the constant
    - 2: (optional) the python type to cast the value to. One of the following:
        - int
        - boolean
        - string
        - float
        - json
- *explanation:* 

    Used when you want the apply the same value to every matching field. You can optionally specify the type of the value and the extractor will attempt to cast it. If no cast type is set, the value will be treated as a string. Typically the schema for the output field will dictate the type. It can also be useful in creating empty stuctures for required fields using the json cast. In the examples you can see the various usages.

- *examples:*
```json
[
    ["#!constant#1#int", "Person.revision"],
    ["#!constant#registered", "Patient.status"],
    ["#!constant#pending_approval#string", "Message.approved"],
    ["#!constant#false#boolean", "Message.is_public"],
    ["#!constant#{\"received\":[], \"sent\":[]}#json", "Queue.archived"],
]
```
---

##### Entity Reference
- *call:* `#!entity-reference`
- *args:*
    - 1: The jsonpath for the resource in the constructed entities.
    - 2: (optional) An anchor reference in the source to the output entity
    - 3: (optional) An anchor reference in the source to the referenced entity
- *explanation and example:*

    The simple case (not using the optional anchor references) of entitiy reference looks at the output of an Entity created in a previous mapping set and copies the value of the field. This is often required when an ID is generated for an entity during extraction, and a reference must be kept using that new ID from other entities.

    For example, one might want to reference the newly created ID of a house in each resident's record.

    Previous Output Entity State:
        People

    ```json
    [
        {"name" : "Buster", "last_name": "Keaton"},
        {"name" : "Grace", "last_name": "Keaton"},
        {"name": "Ace", "last_name": "Keaton"},
        {"name": "Franklin", "last_name": "Keaton"}
    ]
    ```
        Houses

    ```json
    [
        {"id": "e08bafe3-f9af-4412-8e00-93acfc0d68ea", "address": "1000 Chortle Way"}
    ]
    ```

    Mapping:
    ```json  
    [
        "#!entity-reference#$.House[*].id",
        "Person.house"
    ]
    ```
    
    New Output Entity State:
        - People

    ```json
    [
        {"name" : "Buster", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"},
        {"name" : "Grace", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"},
        {"name": "Ace", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"},
        {"name": "Franklin", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"}
    ]
    ```
        - Households

    ```json
    [
        {"id": "e08bafe3-f9af-4412-8e00-93acfc0d68ea", "address": "1000 Chortle Way"}
    ]
    ```
    Using the reference anchors would be a requirement when there are complex relationships in the source data that need to be respected in the extracted entities. For example look at this source data.
    ```json
    {
        "households": [
            {
            "names": [
                "Larry",
                "Curly"
            ],
            "address": "74 Whyioughta St.",
            "number1": 1,
            "number2": 2
            },
            {
            "names": [
                "Moe"
            ],
            "address": "1600 Ipoke Ave",
            "number1": 3
            }
        ]
    }
    ```

    At our current step in extraction, we have all the information we need, except for a reference for the house of each person.

    Stooges:
    ```json
    [
        {
            "id": "a7a1f889-9223-44a2-bbea-b41a415c2989",
            "name": "Larry",
            "number": 1
        },
        {
            "id": "40188061-1942-4041-ae1c-1e1d99221698",
            "name": "Curly",
            "number": 2
        },
        {
            "id": "767f38e8-ce3c-41ee-bd4f-cc1c41bbbde9",
            "name": "Moe",
            "number": 3
        }
    ]
    ```
    Houses:
    ```json
    [
        {
            "id": "2aff48d8-917a-4c9b-814d-99639a220773",
            "address": "74 Whyioughta St."
        },
        {
            "id": "a4354016-1a5a-47ef-9d14-01217f33ff2e",
            "address": "1600 Ipoke Ave"
        }
    ]
    ```
    So, using #!entity-reference, how can we make sure everyone is assigned to the proper house? An anchor reference.
    The first argument should be the path within the source that describes the output entity, in this case a Person. A path that best represents a person in the source is `households[*].names[*]`. The second argument decribes the source of the information in the source document, in this case it's a House, so the proper path would be `households[*]`. As an full command, we get:
    
    ```
    src:    #!entity-reference#House[*].id#households[*].names[*]#households[*]
    dst:    Person.house
    ```
    The new values of the Stooges will have them properly referenced to their respective houses:
    ```json
    [
        {
            "id": "a7a1f889-9223-44a2-bbea-b41a415c2989",
            "name": "Larry",
            "number": 1,
            "house": "2aff48d8-917a-4c9b-814d-99639a220773"
        },
        {
            "id": "40188061-1942-4041-ae1c-1e1d99221698",
            "name": "Curly",
            "number": 2,
            "house": "2aff48d8-917a-4c9b-814d-99639a220773"
        },
        {
            "id": "767f38e8-ce3c-41ee-bd4f-cc1c41bbbde9",
            "name": "Moe",
            "number": 3,
            "house": "a4354016-1a5a-47ef-9d14-01217f33ff2e"
        }
    ]
    ```

    Notice that Larry and Curly still live together, and Moe still lives alone.




---

<a name="extractor-mechanism"></a>
## Extractor Mechanism

As stated previously, Mapping instruction sets are executed in order. If the extractor encounters an error on an instruction, it caches that instuction it and continues down the list. Once finished with the list, it will reattempt the instuctions that had errors. It will continue to retry until either all instuctions have been completed _or_ a round occurs where none of the cached erroneous instuctions were able to be completed. If there are errors at the end of extraction, the errors are reported.

Let's introduce some new artifacts so we can illustrate the process from the extractor point of view.

<details open>
    <summary><i>Input <b>(Hide/Show)</b></i></summary>
    
```json
{
    "family_name": "Keaton",
    "address":"1000 Chortle Way",
    "adults": [
        {"name": "Buster"},
        {"name": "Grace"}
    ],
    "children" : [
        {"name": "Ace"},
        {"name": "Franklin"}
    ]
}
```

</details>
<details open>
    <summary><i>Schemas <b>(Hide/Show)</b></i></summary>

```json
[
  {
    "name": "Person",
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
        "type": "string"
      },
      {
        "name": "house",
        "type": "string",
        "jsonldPredicate": {
          "_id": "eha.aether.jokes.House",
          "_type": "@id"
        }
      }
    ],
    "namespace": "eha.aether.jokes"
  },
  {
    "name": "House",
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

</details>

##### Steps

Let's start with a suboptimal mappings

<details open>
    <summary><i>Mapping <b>(Hide/Show)</b></i></summary>

```json
[
  [
    "#!entity-reference#$.House[*].id",
    "Person.house"
  ],
  [
    "$.family_name",
    "Person.last_name"
  ],
  [
    "$.adults[*].name",
    "Person.name"
  ],
  [
    "$.children[*].name",
    "Person.name"
  ],
  [
    "$.address",
    "House.address"
  ],
  [
    "#!uuid",
    "Person.id"
  ],
  [
    "#!uuid",
    "House.id"
  ]
]
```

</details>

---
<details>
    <summary><i>First Pass Details <b>(Hide/Show)</b></i></summary>

The first thing the extractor does is try to size the output requirements. In this case, based on the mappings and input, we can figure out that there will be 5 output entities; 4 `People` and 1 `Household`. We'll refer to the current state of the output at each mapping step.

_Starting Objects_

People
```json
[
    {},
    {},
    {},
    {}
]
```
Households
```json
[
    {}
]
```

Instruction

```json
  [
    "#!entity-reference#$.House[*].id",
    "Person.house"
  ]
```
_Resulting Objects_

People
```json
[
    {},
    {},
    {},
    {}
]
```
Households
```json
[
    {}
]
```
We don't have anything to reference in `$.House[*.id]` so this fails and is cached.

Instruction

```json
  [
    "$.family_name",
    "Person.last_name"
  ]
```
_Resulting Objects_

People
```json
[
    {"last_name": "Keaton"},
    {"last_name": "Keaton"},
    {"last_name": "Keaton"},
    {"last_name": "Keaton"}
]
```
Households
```json
[
    {}
]
```
This is a straght copy from a path that exists so it succeeds. Since there's only one value from `$.family_name` instead of four, the extractor guesses (correctly) that we should apply the same value to all Person objects. If this were just for the first Person, we could force the extractor to acknowledge this by adding the following instuction directly after: `["#!none", "Person.last_name"]`, which would set the `last_name` of everyone but the first (Buster) to null.

Instruction

```json
  [
    "$.adults[*].name",
    "Person.name"
  ]
```
_Resulting Objects_

People
```json
[
    {"name" : "Buster", "last_name": "Keaton"},
    {"name" : "Grace", "last_name": "Keaton"},
    {"last_name": "Keaton"},
    {"last_name": "Keaton"}
]
```
Households
```json
[
    {}
]
```

Again, this is a straight copy, so it behaves as expected. Do notice that the adults filled the first two spots. Had we switched the order of this instruction with the next one, the children would be first.


Instruction

```json
  [
    "$.children[*].name",
    "Person.name"
  ]
```
_Resulting Objects_

People
```json
[
    {"name" : "Buster", "last_name": "Keaton"},
    {"name" : "Grace", "last_name": "Keaton"},
    {"name": "Ace", "last_name": "Keaton"},
    {"name": "Franklin", "last_name": "Keaton"}
]
```
Households
```json
[
    {}
]
```

Instruction

```json
  [
    "$.address",
    "House.address"
  ]
```
_Resulting Objects_

People
```json
[
    {"name" : "Buster", "last_name": "Keaton"},
    {"name" : "Grace", "last_name": "Keaton"},
    {"name": "Ace", "last_name": "Keaton"},
    {"name": "Franklin", "last_name": "Keaton"}
]
```
Households
```json
[
    {"address": "1000 Chortle Way"}
]
```
We've finally populated `Household` with something.

Instruction

```json
  [
    "#!uuid",
    "Person.id"
  ]
```
_Resulting Objects_

People
```json
[
    {"id": "d10f36af-6fd5-4e41-8711-dc8ba21649d0", "name" : "Buster", "last_name": "Keaton"},
    {"id": "5b3dd77c-769f-413f-a73b-f5ac74d7a3d5", "name" : "Grace", "last_name": "Keaton"},
    {"id": "3e572230-24b6-45c7-b402-9504b4e13e56", "name": "Ace", "last_name": "Keaton"},
    {"id": "62d6585e-d884-48a3-ad9f-53601f238f9a", "name": "Franklin", "last_name": "Keaton"}
]
```
Households
```json
[
    {"address": "1000 Chortle Way"}
]
```
The UUID function adds its values to the id field of `Person` without any issue.


Instruction

```json
  [
    "#!uuid",
    "House.id"
  ]
```
</details>

_Resulting Objects_

People
```json
[
    {"id": "d10f36af-6fd5-4e41-8711-dc8ba21649d0", "name" : "Buster", "last_name": "Keaton"},
    {"id": "5b3dd77c-769f-413f-a73b-f5ac74d7a3d5", "name" : "Grace", "last_name": "Keaton"},
    {"id": "3e572230-24b6-45c7-b402-9504b4e13e56", "name": "Ace", "last_name": "Keaton"},
    {"id": "62d6585e-d884-48a3-ad9f-53601f238f9a", "name": "Franklin", "last_name": "Keaton"}
]
```
Households
```json
[
    {"id": "e08bafe3-f9af-4412-8e00-93acfc0d68ea", "address": "1000 Chortle Way"}
]
```

_Failed Functions_

```json
[
  "#!entity-reference#$.House[*].id",
  "Person.house"
]
```

---
<details>
    <summary><i>Second Pass Details <b>(Hide/Show)</b></i></summary>

Instruction

```json
  [
    "#!entity-reference#$.House[*].id",
    "Person.house"
  ]
```

We can now resolve the Entity Reference as `House[*].id` has a value.

</details>

_Resulting Objects_

People
```json
[
    {"id": "d10f36af-6fd5-4e41-8711-dc8ba21649d0", "name" : "Buster", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"},
    {"id": "5b3dd77c-769f-413f-a73b-f5ac74d7a3d5", "name" : "Grace", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"},
    {"id": "3e572230-24b6-45c7-b402-9504b4e13e56", "name": "Ace", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"},
    {"id": "62d6585e-d884-48a3-ad9f-53601f238f9a", "name": "Franklin", "last_name": "Keaton", "house": "e08bafe3-f9af-4412-8e00-93acfc0d68ea"}
]
```
Households
```json
[
    {"id": "e08bafe3-f9af-4412-8e00-93acfc0d68ea", "address": "1000 Chortle Way"}
]
```


