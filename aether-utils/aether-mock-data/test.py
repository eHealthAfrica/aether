import json
from aether.mocker import MockFn, DataMocker, Generic, MockingManager


def pprint(obj):
    print(json.dumps(obj, indent=2))


def weird(args=None):
    if args:
        return args[::-1]
    return "weird"


def show_mockfn():
    # illustrate how mocker.MockFn can be passed a function and args for later

    m = MockFn(sum, [1, 2])
    f = MockFn(weird, ["dook", "ip"])
    p = MockFn(weird, ["args", "pie"])
    print(m())
    print(f())
    print(p())


def main():

    person = "org.eha.demo.Person"
    location = "org.eha.demo.GeoLocation"

    manager = MockingManager()
    manager.types[location].override_property(
        "latitude", MockFn(Generic.geo_lat))
    manager.types[location].override_property(
        "longitude", MockFn(Generic.geo_lng))

    for x in range(100):
        # Since types are linked, we only need to generate one to spawn linked versions of others
        manager.register(person)
    manager.kill()  # we explicitly clean up our threads


if __name__ == "__main__":
    main()
