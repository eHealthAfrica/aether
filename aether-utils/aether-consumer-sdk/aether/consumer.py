import ast
import io
import json

import kafka
import spavro.schema
import spavro.io
from spavro.datafile import DataFileReader
from spavro.io import DatumReader

from jsonpath_ng import jsonpath, parse


class KafkaConsumer(kafka.KafkaConsumer):

    # Adding these key/ value pairs to those handled by vanilla KAfkaConsumer
    ADDITIONAL_CONFIG = {
        "aether_masking_schema_annotation" : "aetherMaskingLevel",
        "aether_masking_schema_levels" : [0,1,2,3,4],
        "aether_masking_schema_emit_level" : 0,
        "aether_emit_flag_field_path": "$.approved",
        "aether_emit_flag_values": [True]

    }

    def __init__(self, *topics, **configs):
        # Add to DEFAULT_CONFIG
        for k, v in KafkaConsumer.ADDITIONAL_CONFIG.items():
            KafkaConsumer.DEFAULT_CONFIG[k] = v
        # Items not in either default or additional config raise KafkaConfigurationError on super
        super(KafkaConsumer, self).__init__(*topics, **configs)

    def get_approval_filter(self, schema):
        check_condition_path = self.config.get("aether_emit_flag_field_path")
        pass_conditions = self.config.get("aether_emit_flag_values")
        check = None
        if isinstance(pass_conditions, list):
            check = lambda x : x in pass_conditions
        else:
            check = lambda x: x is pass_conditions
        expr = parse(check_condition_path)
        def approval_filter(msg):
            values = [match.value for match in expr.find(msg)]
            if not values:
                return False
            return check(values[0])  # We only check the first matching path/ value
        return approval_filter

    def get_mask_from_schema(self, schema):
        return None

    def mask_message(self, msg, mask=None):
        if not mask:
            return msg
        pass

    def poll_and_deserialize(self, timeout_ms=0, max_records=None):
        result = {}
        last_schema = None
        mask = None
        approval_filter = lambda x : True
        partitioned_messages = self.poll(timeout_ms, max_records)
        if partitioned_messages:
            for part, packages in partitioned_messages.items():  # we don't worry about the partitions for now
                partition_result = []
                for package in packages: # a package can contain multiple messages serialzed with the same schema
                    package_result = {
                        "schema": None,
                        "messages" : []
                    }
                    schema = None
                    obj = io.BytesIO()
                    obj.write(package.value)
                    reader = DataFileReader(obj, DatumReader())

                    # We can get the schema directly from the reader.
                    # we get a mess of unicode that can't be json parsed so we need ast
                    raw_schema = ast.literal_eval(str(reader.meta))
                    schema = raw_schema.get("avro.schema")
                    if not schema:
                        last_schema = None
                        mask = None
                        approval_filter = lambda x : True
                    if schema != last_schema:
                        last_schema = schema
                        package_result["schema"] = schema
                        # prepare mask and filter
                        approval_filter = self.get_approval_filter(schema)
                        mask = self.get_mask_from_schema(schema)
                    else:
                        package_result["schema"] = last_schema
                    for x, msg in enumerate(reader):
                        # do something with the individual messages
                        processed_message = self.mask_message(msg, mask)
                        if approval_filter(processed_message):
                            package_result["messages"].append(processed_message)

                    obj.close()  # don't forget to close your open IO object.
                    if package_result.get("schema") or len(package_result["messages"]) > 0:
                        partition_result.append(package_result)
                if len(partition_result) > 0:
                    result[part] = partition_result
        return result

    def seek_to_beginning(self):
        self.poll(timeout_ms=100, max_records=1)
        super(KafkaConsumer, self).seek_to_beginning()
