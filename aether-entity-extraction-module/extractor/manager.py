# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import collections
import concurrent.futures
import threading
from .utils import get_from_redis_or_kernel, KERNEL_ARTEFACT_NAMES
from .entity_extraction import extract_create_entities


class ExtractionManager():

    SUBMISSION_QUEUE = collections.deque()
    PROCESSED_SUBMISSIONS = collections.deque()
    PROCESSED_ENTITIES = collections.deque()
    is_extracting = False

    def add_to_queue(self, submission):
        if submission:
            self.SUBMISSION_QUEUE.appendleft(submission)
            if not self.is_extracting:
                extraction_thread = threading.Thread(target=self.process, name='extraction-thread')
                extraction_thread.start()
                self.is_extracting = True

    def entity_extraction(self, submission):
        # get artifacts from redis
        # if not found on redis, get from kernel and cache on redis
        # if not found on kernel ==> flag submission as invalid and skip extraction

        mapping_ids = submission.data[KERNEL_ARTEFACT_NAMES.mappings]
        for mapping_id in mapping_ids:
            schemas = {}
            mapping = get_from_redis_or_kernel(
                mapping_id,
                KERNEL_ARTEFACT_NAMES.mappings,
                submission.tenant
            )
            if mapping and mapping[KERNEL_ARTEFACT_NAMES.schemadecorators]:
                schemadecorator_ids = mapping[KERNEL_ARTEFACT_NAMES.schemadecorators]
                schema_decorators = mapping['definition']['entities']
                for shemadecorator_id in schemadecorator_ids:
                    sd = get_from_redis_or_kernel(
                        shemadecorator_id,
                        KERNEL_ARTEFACT_NAMES.schemadecorators,
                        submission.tenant
                    )
                    schema_definition = None
                    if sd and sd[KERNEL_ARTEFACT_NAMES.schema_definition]:
                        schema_definition = sd[KERNEL_ARTEFACT_NAMES.schema_definition]
                    elif sd and sd[KERNEL_ARTEFACT_NAMES.single_schema]:
                        schema = get_from_redis_or_kernel(
                            sd[KERNEL_ARTEFACT_NAMES.single_schema],
                            KERNEL_ARTEFACT_NAMES.schemas,
                            submission.tenant
                        )
                        if schema and schema['definition']:
                            schema_definition = schema['definition']

                    if schema_definition:
                        schemas[sd['name']] = schema_definition

            # perform entity extraction
            _, entities = extract_create_entities(
                submission_payload=submission.data['payload'],
                mapping_definition=mapping['definition'],
                schemas=schemas,
            )

            for entity in entities:
                schemadecorator_name = entity.schemadecorator_name
                schemadecorator = schema_decorators[schemadecorator_name]
                entity_instance = {
                    'payload': entity.payload,
                    'status': entity.status,
                    'schemadecorator': schemadecorator,
                    'submission': submission.id,
                    'mapping': mapping_id,
                    'mapping_revision': mapping['revision'],
                }

        # this should include in the submission payload the following properties
        # generated during the extraction:
        # - ``aether_errors``, with all the errors that made not possible
        #   to create the entities.
        # - ``aether_extractor_enrichment``, with the generated values that allow us
        #   to re-execute this process again with the same result.

            print('ENTITIES', entities)


        # update submission entry

        self.PROCESSED_ENTITIES.appendleft(submission)
        # print(f'processed {submission}', len(self.SUBMISSION_QUEUE))

    def process(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            while self.SUBMISSION_QUEUE:
                executor.submit(self.entity_extraction, self.SUBMISSION_QUEUE.pop())
        if self.SUBMISSION_QUEUE:
            self.process()
        else:
            self.is_extracting = False
