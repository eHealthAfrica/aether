import unittest
import sys
import traceback
import json
from . import (
    kernel_url,
    kernel_credentials,
    project_name,
    project_obj,
    schema_objs,
    project_schema_objs,
    mapping_obj,
    submission_obj
)
from .. import client


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
                KernelClientCase.client = client.KernelClient(kernel_url)
            except KeyError:
                pass
            try:
                fake_credentials = {"missing": "values"}
                KernelClientCase.client = client.KernelClient(kernel_url, **fake_credentials)
            except KeyError:
                pass
            try:
                KernelClientCase.client = client.KernelClient(kernel_url, **kernel_credentials)
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
        name = project_obj.get("name")
        client.Resource.Project.add(project_obj)
        a_str = str(client.Resource['Project'])
        assert(a_str is not None)
        assert(len([i for i in self.client.Resource.Project]) > 0), "Couldn't iterate projects"
        project = self.client.Resource.Project.get(name)
        assert(len([i for i in project.info()]) > 0)
        assert(project.get())
        assert(project.info("id"))
        project_id = project.id
        assert(project is not None), "Project was not created"
        assert(name == project.name), "Project name not accessable by dot convention"
        assert(name == project.get("name")), "Project name not accessable by .get()"
        assert(str(project) is not None)
        project.revision = "2"
        project.update()
        assert(project.revision == "2")
        try:
            project.get("imaginary_value")
        except KeyError:
            pass
        except Exception:
            self.fail("should not accept imaginary_value as a key")
        else:
            self.fail("imaginary_value should raise an exception")
        KernelClientCase.project_id = project.get("id")

        def name(obj):
            return obj.get("name") == project_name

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

        def wrong_name(obj):
            return obj.get("name") == "FAKE"+project_name

        matches = client.Resource.Project.search(wrong_name)
        assert(len([i.name for i in matches]) == 0), "Search for missing value should fail."

    def step2_schemas(self):
        if not KernelClientCase.project_id:
            self.fail("Prerequisite test failed. Stopping")
        client = KernelClientCase.client
        for obj in schema_objs:
            name = obj.get("name")
            client.Resource.Schema.add(obj)
            schema = client.Resource.Schema.get(name)
            _id = schema.id
            same_schema = client.Resource.Schema.get(_id)
            assert(schema == same_schema), "Schema should be gettable by name or id"
            assert(_id is not None), "ID should be accessable by .id"
            _id = schema.get("id")
            assert(_id is not None), "ID should be accessable by .get('id')"
            KernelClientCase.schema_ids[_id] = name

    def step3_project_schemas(self):
        client = KernelClientCase.client
        project_id = KernelClientCase.project_id
        schemas = KernelClientCase.schema_ids
        for x, obj in enumerate(project_schema_objs):
            name = obj.get('name')
            schema_id = [k for k, v in schemas.items() if v == "My"+name][0]
            assert(schema_id is not None)
            obj["schema"] = schema_id
            obj["project"] = project_id
            client.Resource.ProjectSchema.add(obj)
            schema = client.Resource.ProjectSchema.get(name)
            assert(schema is not None), "ProjectSchema should be available immediately"
            _id = schema.id
            same_schema = client.Resource.ProjectSchema.get(_id)
            if x == 0:
                same_schema['is_encrypted'] = True
                client.Resource.ProjectSchema.update(same_schema)
                same_schema = client.Resource.ProjectSchema.get(_id)
                assert(same_schema['is_encrypted'] is not schema['is_encrypted']), (
                    "Schema didn't update")
            else:
                assert(schema == same_schema), "Schema should match"
            assert(_id is not None)
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
        mapping = client.Resource.Mapping.get(name)
        assert(mapping is not None), "Couldn't add mapping"
        assert(len([i for i in client.Resource.Mapping]) > 0), "Couldn't iterate mappings"
        KernelClientCase.mapping_id = mapping.get('id')

    def step5_submission(self):
        client = KernelClientCase.client
        mapping_id = KernelClientCase.mapping_id

        def ignore(obj):
            return False

        mapping = client.Resource.Mapping.get(mapping_id)
        submission = submission_obj
        endpoint = client.Submission.get(mapping.name)
        assert([i for i in client.Submission] is not []), "Should be iterable submissions"
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
            "Could't get submissions endpoint for mapping id %s" % mapping.id)
        endpoint = client.Submission.get(mapping.id)
        assert(endpoint is not None), (
            "Could't get submissions endpoint for mapping name %s" % mapping.name)
        # submit the same data 10 times!
        for x in range(10):
            res = endpoint.submit(submission)
        # make sure we made some entities
        assert(res.get("entities_url") is not None), "No entitites were created"
        subs = endpoint.get(filter_func=ignore)
        assert(len([1 for i in subs]) == 0), "Filter didn't work"
        subs = endpoint.get(filter_func=None)
        assert(len([1 for i in subs]) >= 10), "Couldn't iterate over submission"
        # Get a submission by id
        a_submission = next(endpoint.get())
        _id = a_submission.get("id")
        match = endpoint.get(id=_id)
        assert(match == a_submission)

    def step6_entities(self):
        client = KernelClientCase.client

        people = client.Entity.Person
        assert (client.Entity.info() is not None), "Info should return basic information"
        assert(people.info() is not None), "Info should return basic information"
        try:
            x = people.missing_attribute
            if x:
                print(x)  # to appease the linter
        except AttributeError:
            pass
        else:
            self.fail("missing_attribute should throw an error")

        def age(obj):
            payload = obj.get('payload')
            if not payload:
                return False
            age = payload.get('age')
            if not age:
                return False
            return int(age) < 40

        a_person = next(people.get())
        _id = a_person.get('id')
        same_person = client.Entity[_id]
        assert(a_person == same_person)

        population = sum([1 for person in people])
        young_people = people.get(filter_func=age)
        young_pop = sum([1 for person in young_people])
        assert(young_pop < population), "Filter didn't work, should be fewer young people."
        # make one person old
        young_people = people.get(filter_func=age)
        for person in young_people:
            person['payload']['age'] = 45
            res = people.update(person)
            assert(res.get('url') is not None), "Couldn't post updated entity"
            break
        young_people = people.get(filter_func=age)
        new_young_pop = sum([1 for person in young_people])
        assert(new_young_pop < young_pop)
        # test various patterns to access an entity
        test_person = next(people.get())
        test_id = test_person.get('id')
        assert(test_person is not None), "Couldn't grab a person from the generator"
        # Entity
        person = client.Entity.Person.get(id=test_id)
        assert(person == test_person)
        person = client.Entity.Person.get(id="fake")
        assert(person is None), "A bad ID shouldn't return an entity"
        # ProjectSchema
        person = client.Entity.MyPerson.get(id=test_id)
        assert(person == test_person)
        # Project
        person = client.Entity.get(project_name).get(id=test_id)
        assert(person == test_person)

        # Mapping
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

        personal_submission = test_person.get('submission')

        a_mapping_id = next(iter(client.Submission.get()))
        endpoint = client.Submission.get(a_mapping_id)
        a_submission = endpoint.get(id=personal_submission)
        assert(a_submission is not None)

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
