from aether.client import KernelClient
import pytest
from time import sleep

kernel_url = "http://kernel-test:9000/v1"

kernel_credentials ={
    "username": "admin-kernel",
    "password": "adminadmin",
}

kernel_retry = 3
kernel_retry_time = 5

@pytest.fixture(scope="session")
def aether_client():
    for x in range(kernel_retry):
        try:
            client = KernelClient(kernel_url, **kernel_credentials)
            return client
        except Excpetion as err:
            sleep(kernel_retry_time)
            pass

    raise ConnectionError("Could not connect to Aether Kernel on url: %s" % kernel_url)

@pytest.fixture(scope="module")
def existing_projects(aether_client):
    return [i for i in aether_client.Resource.Project]

@pytest.fixture(scope="module")
def existing_projectschemas(aether_client):
    return [i for i in aether_client.Resource.ProjectSchema]

@pytest.fixture(scope="module")
def existing_entities(aether_client, existing_projectschemas):
    for ps in existing_projectschemas:
        print(ps)


