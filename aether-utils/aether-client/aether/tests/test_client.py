# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

import json
import os
import random
import sys
import traceback
import unittest

from . import (
    kernel_url,
    project_name,
    project_obj,
    schema_objs,
    project_schema_objs,
    mapping_obj,
    submission_obj
)
from .. import client as _client


def pprint(obj):
    print(json.dumps(obj, indent=2))


class KernelClientCase(unittest.TestCase):

    # These integration tests run against an instance of Aether Kernel
    # The goal is to make sure the client functions on client or
    # Kernel upgrade.

    project_id = None
    client = None
    schema_ids = {}
    ps_ids = {}

    def setUp(self):
        # Connect to the client
        self.failures = []
        self.success = 0
        try:
            if not KernelClientCase.client:
                raise Exception()
        except Exception as err:
            try:
                KernelClientCase.client = _client.KernelClient(kernel_url)
            except AttributeError:
                pass
            try:
                kernel_username = os.environ['KERNEL_USERNAME']
                kernel_password = os.environ['KERNEL_PASSWORD']
                KernelClientCase.client = _client.KernelClient(
                    kernel_url,
                    username=kernel_username,
                    password=kernel_password,
                )
                print("Connected client to Aether on %s" % kernel_url)
            except Exception as e:
                print(e)
                self.fail("Could not properly connect to Aether Kernel / setup client")

    def tearDown(self):
        # report success or failure
        if self.failures:
            for i in self.failures:
                print(i)
            self.fail("Integration test failed with %s faults." % len(self.failures))
        else:
            print("Completed %s tasks without issue." % self.success)

    def _steps(self):
        # iterator to step through sequential test steps
        for name in sorted(dir(self)):
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_steps(self):
        # The entrypoint for the test functions.
        for name, step in self._steps():
            try:
                step()
                self.success += 1
                sys.stdout.write(".")  # cheesey dot replicating normal unittest behavior
            except Exception as e:
                print(traceback.format_exc())
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.failures.append((step, exc_type))
                print("Fault: {} failed ({}: {})".format(step, type(e), e))

    def step1_project(self):

        client = KernelClientCase.client

        # Make a project and assert some things about its creation
        client.Resource.Project.add(project_obj)
        name = project_obj.get("name")
        a_str = str(client.Resource['Project'])
        project = self.client.Resource.Project.get(name)
        project_id = project.id
        assert(a_str is not None), "Couldn't stringify the project endpoint info"
        assert(len([i for i in self.client.Resource.Project]) > 0), "Couldn't iterate projects"
        assert(len([i for i in project.info()]) > 0), "Project info was missing"
        assert(project.get())
        assert(project.info("id"))
        assert(project is not None), "Project was not created"
        assert(name == project.name), "Project name not accessable by dot convention"
        assert(name == project.get("name")), "Project name not accessable by .get()"
        assert(str(project) is not None)

        # Update the project and make sure it worked
        project.revision = "2"
        project.update()
        assert(project.revision == "2"), "Version update didn't take"
        try:
            project.get("imaginary_value")
        except AttributeError:
            pass
        except Exception:
            self.fail("should not accept imaginary_value as a key")
        else:
            self.fail("imaginary_value should raise an exception")
        KernelClientCase.project_id = project.get("id")

        # create a function to pass as a search filter
        def name(obj):
            return obj.get("name") == project_name

        # search for the created project using various methods
        matches = client.Resource.Project.search(name)
        assert(len([i.name for i in matches]) > 0), "Search for known project failed."
        match = client.Resource.Project[project_id]
        assert(match is not None), "Search for known project failed."
        assert(str(client.Resource.Project) is not None), "Should be stringable."
        assert(client.Resource.Project.names() is not None)
        assert(client.Resource.Project.ids() is not None)
        try:
            client.Resource.Project["missing"]
        except AttributeError:
            pass
        else:
            self.fail("missing attribue not caught")
        # Make a bad filter that should find nothing

        def wrong_name(obj):
            return obj.get("name") == "FAKE"+project_name
        matches = client.Resource.Project.search(wrong_name)
        assert(len([i.name for i in matches]) == 0), "Search for missing value should fail."

    def step2_schemas(self):
        client = KernelClientCase.client
        # Create schemas from our definitions
        for obj in schema_objs:
            name = obj.get("name")
            # Add the schema
            client.Resource.Schema.add(obj)
            # Then retrieve it by name
            schema = client.Resource.Schema.get(name)
            _id = schema.id
            # Then retrieve it by id
            same_schema = client.Resource.Schema.get(_id)
            assert(schema == same_schema), "Schema should be gettable by name or id"
            assert(_id is not None), "ID should be accessable by .id"
            _id = schema.get("id")
            assert(_id is not None), "ID should be accessable by .get('id')"
            KernelClientCase.schema_ids[_id] = name

    def step3_project_schemas(self):
        # Connect to Client and retreive previously created reference values
        client = KernelClientCase.client
        project_id = KernelClientCase.project_id
        schemas = KernelClientCase.schema_ids

        for x, obj in enumerate(project_schema_objs):
            name = obj.get('name')
            schema_id = [k for k, v in schemas.items() if v == "My"+name][0]
            assert(schema_id is not None)
            obj["schema"] = schema_id
            obj["project"] = project_id
            # create a project schema based on a previously created schema
            client.Resource.ProjectSchema.add(obj)
            # get retrieve by name
            schema = client.Resource.ProjectSchema.get(name)
            assert(schema is not None), "ProjectSchema should be available immediately"
            # get an attribute by __getattr__
            _id = schema.id
            # get retrieve by id
            same_schema = client.Resource.ProjectSchema.get(_id)
            # for the first one, we update a value in the record
            if x == 0:
                same_schema['is_encrypted'] = True
                client.Resource.ProjectSchema.update(same_schema)
                same_schema = client.Resource.ProjectSchema.get(_id)
                assert(same_schema['is_encrypted'] is not schema['is_encrypted']), (
                    "Schema didn't update")
            else:
                assert(schema == same_schema), "Schema should match"
            assert(_id is not None)
            # get an attribute by get
            _id = schema.get("id")
            assert(_id is not None)
            KernelClientCase.ps_ids[_id] = name

    def step4_mapping(self):
        client = KernelClientCase.client
        name = mapping_obj.get('name')
        # massaging mapping definition to add UUIDs from proper project schemas
        ps_dict = {v: k for k, v in KernelClientCase.ps_ids.items()}
        definition = mapping_obj['definition']
        definition['entities'] = ps_dict
        mapping_obj['definition'] = definition
        mapping_obj['project'] = KernelClientCase.project_id
        # all done! now submit it
        client.Resource.Mapping.add(mapping_obj)
        # retrieve the mapping by name
        mapping = client.Resource.Mapping.get(name)
        assert(mapping is not None), "Couldn't add mapping"
        assert(len([i for i in client.Resource.Mapping]) > 0), "Couldn't iterate mappings"
        KernelClientCase.mapping_id = mapping.get('id')

    def step5_submission(self):
        client = KernelClientCase.client
        mapping_id = KernelClientCase.mapping_id
        mapping = client.Resource.Mapping.get(mapping_id)

        # find the endpoint for submission for our mapping using various methods.
        # get an endpoint for submission to the mapping we created by the mapping name
        endpoint = client.Submission.get(mapping.name)
        assert(len([1 for sub in endpoint]) == 0), "Should be 0 existing submissions"
        assert([1 for ep in client.Submission] is not []), "Submissions endpoints are iterable"
        assert(client.Submission[mapping.id] is not None), (
            "Should be able to getattr from submissions collection")
        try:
            client.Submission["not_a real value"]
        except AttributeError:
            pass
        else:
            self.fail("bad value should throw error")
        assert(len([1 for i in client.Submission.names()]) > 0)
        assert(len([1 for i in client.Submission.ids()]) > 0)
        assert(endpoint is not None), (
            "Could't get endpoint for mapping id %s" % mapping.id)
        # get the same endpoint by mapping id
        endpoint = client.Submission.get(mapping.id)
        assert(endpoint is not None), (
            "Could't get endpoint by mapping id %s" % mapping.id)

        # Submit data to our submissions endpoint
        res = None
        # submit the same data 10 times!
        for x in range(10):
            res = endpoint.submit(submission_obj)  # our pre-created fake submission
        # get same endpoint by mapping id
        endpoint = client.Submission.get(mapping.id)
        assert(len([1 for i in endpoint]) == 10), "Should be 10 existing submissions"

        # make sure we made some entities (check last submission return value)
        assert(res.get("entities_url") is not None), "No entitites were created"
        # make a filter function that ignores everything

        def ignore(obj):
            return False
        subs = endpoint.get(filter_func=ignore)
        assert(len([1 for sub in subs]) == 0), "Filter didn't work"
        subs = endpoint.get(filter_func=None)
        assert(len([1 for sub in subs]) == 10), "Couldn't iterate over submission"
        # Get the first submission
        a_submission = next(endpoint.get())
        _id = a_submission.get("id")
        # Get another copy of the submission by id
        match = endpoint.get(id=_id)
        assert(match == a_submission)

    def step6_entities(self):
        client = KernelClientCase.client

        # Get basic information about the endpoint (really just a name)
        assert (client.Entity.info() is not None), "Info should return basic information"

        # Access all entities of a type "Person"
        people = client.Entity.Person
        assert(people.info() is not None), "Info should return basic information"
        # Try go get a missing person from the endpoint
        try:
            x = people.missing_person
            if x:
                raise KeyError(x)  # to appease the linter
        except AttributeError:
            pass
        else:
            self.fail("missing_attribute should throw an error")

        # Grab the first person from the endpoint
        a_person = next(people.get())
        _id = a_person.get('id')
        # Get them from the entity endpoint by id and check for equality
        same_person = client.Entity[_id]
        assert(a_person == same_person)

        # Make a filter that only returns people under 40
        def youth_filter(obj):
            payload = obj.get('payload', {})
            age = payload.get('age', None)
            if not age:
                return False
            return int(age) < 40

        # get all the young people
        population = sum([1 for person in people.get()])
        assert(population > 0), "Should be able to access whole population by list comprehension."
        young_people = people.get(filter_func=youth_filter)
        young_pop = sum([1 for person in young_people])
        assert(young_pop > 0), "Filter didn't work, should be some young people."
        assert(young_pop < population), "Filter didn't work, should be fewer young people."

        # make one young person very old & run tests on them
        poor_sap = next(people.get(filter_func=youth_filter))
        poor_sap['payload']['age'] = 110
        res = people.update(poor_sap)
        assert(res.get('url') is not None), "Couldn't post updated entity"
        young_people = people.get(filter_func=youth_filter)
        new_young_pop = sum([1 for person in young_people])
        assert(new_young_pop < young_pop), \
            "nyw: %s should be less than old_yp %s" % (new_young_pop, young_pop)

        # test various patterns to access an entity
        test_person = next(people.get())
        test_id = test_person.get('id')
        assert(test_person is not None), "Couldn't grab a person from the generator"
        person = client.Entity.Person.get(id=test_id)  # using explicit id= filter
        assert(person == test_person)
        person = client.Entity.Person.get(id="fake")  # fail to get a person using a bad id
        assert(person is None), "A bad ID shouldn't return an entity"
        # ProjectSchema
        person = client.Entity.MyPerson.get(id=test_id)  # get an object with specific PS & id
        assert(person == test_person)
        # Project
        person = client.Entity.get(project_name).get(id=test_id)  # get by project and id
        assert(person == test_person)

        # Mapping
        # It starts to get silly in this section, but all the idioms should work.
        test_person = next(client.Entity.get("Person").get())
        other_person = client.Entity["Person"].get(id=test_person.get('id'))
        third_person = client.Entity.Person.get(id=test_person.get('id'))
        assert(test_person == other_person == third_person), (
            "These access methods should be the same")
        try:
            missing_person = client.Entity["MissingPerson"]
            if missing_person:  # to appease the linter
                pass
        except AttributeError as ae:
            pass
        else:
            self.fail("Should have been missing and thrown an AttributeError: %s" % missing_person)

        # We use roundabout methods to find the submission that created one of our entities
        personal_submission = test_person.get('submission')  # the submission that made it
        submission_endpoint = next(client.Submission.get())  # There's only one endpoint/mapping
        a_mapping_id = submission_endpoint.mapping_id        # We can get the mapping from it...
        a_submission = submission_endpoint.get(id=personal_submission)  # and our submission
        assert(a_submission is not None), "We should get our submission by its id"

        # Now we'll perform entity searches using lots of different parameter types

        type_names = [
            "TestProject",
            "MyPerson",
            "Person",
            "MyHousehold",
            a_mapping_id,
            personal_submission
        ]
        ps = client.Resource.ProjectSchema
        for type_name in type_names:
            if type_name == type_names[0]:
                matches = client.Entity.get(key=type_name, search_type="project")
            else:
                matches = client.Entity.get(type_name)
            counts = {}
            for match in matches:
                _id = match.get('projectschema')
                name = ps.get(_id).name
                counts[name] = counts.get(name, 0) + 1
            assert(counts)

            if type_name == type_name[-1]:
                assert(counts == {'Household': 1, 'Location': 1, 'Person': 6})

    def step7_generic_tests(self):
        client = KernelClientCase.client
        bad_url = client.url_base + "/not_found"
        assert(client.get(bad_url) is None)

    def step90_delete_entities(self):
        client = KernelClientCase.client
        entity_ids = [i.get("id") for i in client.Entity]
        remaining_entities = sum([1 for i in client.Entity])
        assert(len(entity_ids) == remaining_entities), "These should match!"
        ids = []
        # Gather the ids and then delete them. Don't do it inside the iterator.
        # Pagination will get messed up and you'll miss some.
        for x, _id in enumerate(entity_ids):
            ids.append(_id)
            method = random.choice([True, False])
            if method:
                entity = client.Entity[_id]
                client.Entity.delete(entity)
            else:
                client.Entity.delete(_id)
        assert(len(ids) == len(set(ids)))
        remaining_entities = sum([1 for i in client.Entity])
        assert(remaining_entities == 0), "Entities survived deletion : %s" % remaining_entities

    def step91_delete_mapping(self):
        client = KernelClientCase.client
        name = mapping_obj.get('name')
        mapping = client.Resource.Mapping.get(name)
        assert(mapping is not None)
        ok = mapping.delete()
        assert(ok.get('ok'))
        ok = mapping.delete()
        assert(not ok.get('ok'))

    def step92_delete_project_schemas(self):
        client = KernelClientCase.client
        client.Resource.ProjectSchema.load()
        for schema_id in KernelClientCase.ps_ids.keys():
            schema = client.Resource.ProjectSchema.get(schema_id)
            assert(schema is not None), "Schema with id %s not found" % schema_id
            ok = schema.delete()
            assert(ok.get('ok'))
            ok = schema.delete()
            assert(not ok.get('ok'))

    # deleting a schema kills associated project_schemas!
    def step93_delete_schemas(self):
        client = KernelClientCase.client
        client.Resource.Schema.load()
        for schema_id in KernelClientCase.schema_ids.keys():
            schema = client.Resource.Schema.get(schema_id)
            assert(schema is not None), "Schema with id %s not found" % schema_id
            ok = schema.delete()
            assert(ok.get('ok'))
            ok = schema.delete()
            assert(not ok.get('ok'))

    # deleting a project will delete all things directly referencing the project
    # including all project_schemas etc...
    # be careful!
    def step94_delete_project(self):
            if not KernelClientCase.project_id:
                self.fail("Prerequisite test failed. Stopping")
            client = KernelClientCase.client
            project_id = KernelClientCase.project_id
            project = client.Resource.Project.get(project_id)
            ok = project.delete()
            assert(ok.get('ok'))
            ok = project.delete()
            assert(not ok.get('ok'))


class ODKClientCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
