from aether.client import KernelClient
import pytest
import sys
from time import sleep

kernel_url = "http://kernel-test:9000/v1"

kernel_credentials = {
    "username": "admin-kernel",
    "password": "adminadmin",
}

kernel_retry = 3
kernel_retry_time = 5


py2 = pytest.mark.skipif(sys.version_info >= (3, 0), reason="Test only required for python2")
py3 = pytest.mark.skipif(sys.version_info <= (3, 0), reason="Test only required for python3")


@pytest.fixture(scope="session")
def aether_client():
    for x in range(kernel_retry):
        try:
            client = KernelClient(kernel_url, **kernel_credentials)
            return client
        except Exception as err:
            sleep(kernel_retry_time)
            print("Couldn't connect to Aether: %s" % (err))
            pass

    raise EnvironmentError("Could not connect to Aether Kernel on url: %s" % kernel_url)


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
