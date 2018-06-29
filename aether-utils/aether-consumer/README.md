# Aether Kafka SDK Features
Aether Output Connectors are a powerful way of feeding foreign systems with data from an Aether instance. Part of our approach with Aether is to provide simple access to powerful functionality without being overly opinionated. With the Aether Connect SDK, we provide a low level Python API to Kafka Topics running on the instance. On top of the base functionality you would expect from a Kafka Consumer, we provide a number of additional features.

  - Fast deserialization of messages with Spavro
  - Value based filtering of whole messages.
  - Exclusion of fields from a read message based on data classification

# SDK Features
The SDK is built on top of the standard [kafka-python] library. The entire API remains intact with the following modifications.

## Deserialization with Spavro

There are many Avro libraries available for python. [Spavro] uses the syntax of the official python2 Avro library, while adding compatibility for Python3, and providing a 15x (de)serialization speed increase via C extensions. To support this functionality, we provide a ```poll_and_deserialize(timeout_ms, max_records)``` method, which mirrors the basic functionality of the ```poll()``` method from the kafka-python library, while providing deserialized messages in the following format:
```json
{
    "topic:{topic}-partition:{partition}" : [
        {
            "schema" : message_schema,
            "messages": [messages]
        }
    ]
}
```
For example, we can poll for the latest 100 messages like this:
```python
    from aet.consumer import KafkaConsumer
    consumer = KafkaConsumer(**config)
    consumer.subscribe('my-topic')

    new_records = consumer.poll_and_deserialize(
                timeout_ms=10,
                max_records=100)

    for parition_key, packages in new_records.items():
        for package in packages:
            schema = package.get('schema')
            messages = package.get('messages')
            if schema != last_schema:
                pass  # Or do something since the schema has changed
            for msg in messages:
                pass  # do something with each message
            last_schema = schema
```

Since any filtering based on the contents of a message require comprehension of the message, to perform any reads that requires filtering, _you must use this method_. Poll will return messages that are not filtered, regardless of consumer setting.

## Filtering Functionality

It is a common requirement to take a subset of the data in a particular topic and make it available to downstream sytems via an Output Connector. There are two general classes of filtering that we support.

- Message Emit Filtering: Filtering of whole messages based on one of the values in the message's fields.
- Field Masking Filtering: Removing some fields from a message based on a classification and privledge system.

## Message Emit Filtering

Filtering of whole messages is based on a field value contained in a message matching one of a set of predefined values. Emit filtering is not controlled strictly by a messages schema. It is controlled by the following configuration values, set through the KafkaConsumer constructor. The only requisite is that a message contain the proper JSONPath.
```python
    {
        "aether_emit_flag_required": True,
        "aether_emit_flag_field_path": "$.approved",
        "aether_emit_flag_values": [True]
    }
```

Emit filtering is enabled by default through  ```"aether_emit_flag_required" : True```. If you messages will not require filtering in this manner, set it to ```False``` Once a message is deserialized, the consumer finds the value housed at the JSONPath ```aether_emit_flag_field_path```. If that value is a member of the set configured in ```aether_emit_flag_values```. A small example, given the default configuration shown above.

```json
{
    "id": "passing_message",
    "values": [1,2,3],
    "approved": true
}
```

This message would be emitted for downstream systems.

```json
{
	"id": "failing_message",
	"values": [1, 2, 3],
	"approved": false
}
```

This message would not be made available, since the value at path ```$.approved``` is ```False``` which is not a member of ```[True]```.

It is not requireed that ```aether_emit_flag_values``` be a boolean. For example this is a valid configuration:

```python
    {
        "aether_emit_flag_field_path": "$.record_type",
        "aether_emit_flag_values": ["routine_vaccination", "antenatal_vaccination"]
    }
```
This message will be emitted.
```json
{
    "id": "passing_message",
    "date": "2018-07-01",
    "record_type': "routine_vaccination"
}
```
This message will _not_ be emitted.
```json
{
    "id": "failing_message",
    "date": "2018-07-01",
    "record_type': "postpartum_followup"
}
```

## Field Masking Filter

It is often a requirement that only a subset of a message be made available to a particular downstream system. In this case, we use field filtering. Field filtering requires an annotation in the Avro Schema of a message type on each field which might need to be stripped. This also implies that we have a information classification system which is appropriate for our data. For example, we could use this scale for the classification of governmental information ```["public", "confidential", "secret", "top secret", "ufos"]``` Where public information is the least sensitive, all the way up to highly classified information about the existence of UFOs.

_Having these classifiers, we can use them in the Avro schema for a message type._
```json
    {
        "fields": [
            {
                "jsonldPredicate": "@id",
                "type": "string",
                "name": "id"
            },
            {
                "type": [
                    "null",
                    "boolean"
                ],
                "name": "publish",
            },
            {
                "type": [
                    "null",
                    "string"
                ],
                "name": "field1",
                "aetherMaskingLevel": "public"
            },
            {
                "type": [
                    "null",
                    "string"
                ],
                "name": "field2",
                "aetherMaskingLevel": "confidential"
            },
            {
                "type": [
                    "null",
                    "string"
                ],
                "name": "field3",
                "aetherMaskingLevel": "secret"
            },
            {
                "type": [
                    "null",
                    "string"
                ],
                "name": "field4",
                "aetherMaskingLevel": "top secret"
            },
            {
                "type": [
                    "null",
                    "string"
                ],
                "name": "field5",
                "aetherMaskingLevel": "ufos"
            },
        ],
        "type": "record",
        "name": "TestTopSecret"
    }
```
Now we have the following message in a topic:
```json
    {
        "id" : "a_guid",
        "publish" : true,
        "field1" : "a",
        "field2" : "b",
        "field3" : "c",
        "field4" : "d",
        "field5" : "e"
    }
```
If we use an emit level of ```"aether_masking_schema_emit_level": "public"``` in the following configuration, only fields with that classification or less (including no classification) will be emitted.
```python
    {
        "aether_emit_flag_required": True,
        "aether_emit_flag_field_path": "$.publish",
        "aether_emit_flag_values": [True],
        "aether_masking_schema_levels" : ["public", "confidential", "secret", "top secret", "ufos"]
        "aether_masking_schema_emit_level": "public"
    }
```
_The following message will be emitted:_
```json
    {
        "id" : "a_guid",
        "publish" : true,
        "field1" : "a"
    }
```
If the rest of the configuration remains, but we use ```"aether_masking_schema_emit_level": "secret"``` the message becomes.
```json
    {
        "id" : "a_guid",
        "publish" : true,
        "field1" : "a",
        "field2" : "b",
        "field3" : "c"
    }
```
In this way, we can have different consumers emitting different versions of the same message to their respective downstream systems.

[kafka-python]: <https://github.com/dpkp/kafka-python>
[spavro]: <https://github.com/pluralsight/spavro>
