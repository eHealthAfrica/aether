## Aether Producer

#### Purpose

The Aether Producer (AP) provides a bridge between the RDBMS world of the kernel, and the message centric world of Kafka. The goal of the AP is to make all entities saved in kernel available in Kafka as quickly and efficiently as possible, so that they may be read by consumers which feed that data to downstream systems.

#### Method of Operation

The AP interacts directly with the kernel database. It polls to keep state on all registered entity types. Once a type is registered, the AP will continuously query the kernel database for new entities that have been added to that type. 
 - By default all entities of the same type are produced to a Kafka topic bearing the name of that entity type. 
 - By default messages adhereing to the same schema are serialized into Avro objects containing between 1 -> 250 messages to save space.

#### Persistence

In kernel, all entities contain a modified datetime field which the AP uses to determine which entities have already been sent to Kafka. The AP refers to this value as an offset, and for each entity type, it maintains a record of the lastest offset that has been accepted by Kafka. On shutdown or failure, the AP will resume polling for at `modified > last_offset`.

#### Control

While normally the producer can be left to run on its own, sometimes for testing or other purposes, one may want to stop the producer, or have it reproduce the contents of a topic. An API has been made available for this purpose. These are the endpoints.

 - `/topics` : Allow a user to see how many individual messages are stored in Kernel and should be in Kafka / available to consumers
 - `/pause?topic={topic}` : Temporarily stop a topic from being produced
 - `/resume?topic={topic}` : Resume production on a paused topic
 - `/rebuild?topic={topic}` : Allow a user to force the producer to delete a topic. Requires a subsequent call to `/resume` to then recreate & repopulate the topic. One cannot pause or resume a topic that's in the process of being rebuilt. `/status` for that topic will indicate it's rebuild status.

To allow for this to operate securely, all endpoints besides /healthcheck require authentication via basic auth. There is only currently one user and the credentials are set through environment.