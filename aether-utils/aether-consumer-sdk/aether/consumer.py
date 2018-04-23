import ast
import io
import json

from kafka import KafkaConsumer as VanillaConsumer
from spavro.datafile import DataFileReader
from spavro.io import DatumReader

from jsonpath_ng import parse


class KafkaConsumer(VanillaConsumer):

    # Adding these key/ value pairs to those handled by vanilla KafkaConsumer
    ADDITIONAL_CONFIG = {
        "aether_masking_schema_annotation": "aetherMaskingLevel",
        "aether_masking_schema_levels": [0, 1, 2, 3, 4, 5],
        "aether_masking_schema_emit_level": 0,
        "aether_emit_flag_field_path": "$.approved",
        "aether_emit_flag_values": [True]
    }

    def __init__(self, *topics, **configs):
        # Add to inherited DEFAULT_CONFIG
        for k, v in KafkaConsumer.ADDITIONAL_CONFIG.items():
            KafkaConsumer.DEFAULT_CONFIG[k] = v
        # Items not in either default or additional config raise KafkaConfigurationError on super
        super(KafkaConsumer, self).__init__(*topics, **configs)

    def get_approval_filter(self):
        check_condition_path = self.config.get("aether_emit_flag_field_path")
        pass_conditions = self.config.get("aether_emit_flag_values")
        check = None
        if isinstance(pass_conditions, list):
            def check(x):
                return x in pass_conditions
        else:
            def check(x):
                return x is pass_conditions
        expr = parse(check_condition_path)

        def approval_filter(msg):
            values = [match.value for match in expr.find(msg)]
            if not len(values) > 0:
                return False
            return check(values[0])  # We only check the first matching path/ value
        return approval_filter

    def get_mask_from_schema(self, schema):
        # This creates a masking function that will be applied to all messages emitted
        # in poll_and_deserialize. Fields that may need to be masked must have in their
        # schema a signifier of their classification level. The jsonpath of that classifier
        # (mask_query) should be the same for all fields in a schema. Within the the message,
        # any field requiring classification should have a value associated with its field
        # level classification. That classification should match one of the levels passes to
        # the consumer (mask_levels). Fields over the approved classification (emit_level) as
        # ordered in (mask_levels) will be removed from the message before being emitted.

        mask_query = self.config.get("aether_masking_schema_annotation")  # classifier jsonpath
        mask_levels = self.config.get("aether_masking_schema_levels")     # classifier levels
        emit_level = self.config.get("aether_masking_schema_emit_level")  # chosen level
        try:
            emit_index = mask_levels.index(emit_level)
        except ValueError:
            raise ValueError("emit_level %s it not a value in range of restrictions: %s" %
                             (emit_level, mask_levels))
        query_string = "$.fields.[*].%s.`parent`" % mask_query  # parent node of matching field
        expr = parse(query_string)
        restricted_fields = [(match.value) for match in expr.find(schema)]
        restriction_map = [[obj.get("name"), obj.get(mask_query)] for obj in restricted_fields]
        failing_values = [i[1] for i in restriction_map if mask_levels.index(i[1]) > emit_index]

        def mask(msg):
            for name, field_level in restriction_map:
                if msg.get(name, None):  # message has a field with classification
                    if field_level in failing_values:  # classification is above threshold
                        msg.pop(name, None)
            return msg
        return mask

    def mask_message(self, msg, mask=None):
        # this applied a mask created from get_mask_from_schema()
        if not mask:
            return msg
        else:
            return mask(msg)

    def poll_and_deserialize(self, timeout_ms=0, max_records=None):
        result = {}
        last_schema = None
        mask = None
        approval_filter = None
        '''
        def approval_filter(x):
            return True
        '''
        partitioned_messages = self.poll(timeout_ms, max_records)
        if partitioned_messages:
            for part, packages in partitioned_messages.items():
                # we don't worry about the partitions for now
                partition_result = []
                # a package can contain multiple messages serialzed with the same schema
                for package in packages:
                    package_result = {
                        "schema": None,
                        "messages": []
                    }
                    schema = None
                    obj = io.BytesIO()
                    obj.write(package.value)
                    reader = DataFileReader(obj, DatumReader())

                    # We can get the schema directly from the reader.
                    # we get a mess of unicode that can't be json parsed so we need ast
                    raw_schema = ast.literal_eval(str(reader.meta))
                    schema = json.loads(raw_schema.get("avro.schema"))
                    if not schema:
                        last_schema = None
                        mask = None

                        def approval_filter(x):
                            return True
                    elif schema != last_schema:
                        last_schema = schema
                        package_result["schema"] = schema
                        # prepare mask and filter
                        approval_filter = self.get_approval_filter()
                        mask = self.get_mask_from_schema(schema)
                    else:
                        package_result["schema"] = last_schema
                    for x, msg in enumerate(reader):
                        # is message is ready for consumption, process it
                        if approval_filter(msg):
                            # apply masking
                            processed_message = self.mask_message(msg, mask)
                            package_result["messages"].append(processed_message)

                    obj.close()  # don't forget to close your open IO object.
                    if package_result.get("schema") or len(package_result["messages"]) > 0:
                        partition_result.append(package_result)
                if len(partition_result) > 0:
                    name = "topic:%s-partition:%s" % (part.topic, part.partition)
                    result[name] = partition_result
        return result

    def seek_to_beginning(self):
        self.poll(timeout_ms=100, max_records=1)
        super(KafkaConsumer, self).seek_to_beginning()
