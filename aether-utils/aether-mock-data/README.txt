This utility library allows for the creation of mock data.
Mock data is random and based on schemas registered with your local Aether instance.
It expectes to find Aether running on kernel.aether.local with default credentials.
It expects for you to have schemas registered either via the Salad Bar or manually.

See test.py for an example running against the Salad Demo.

    To run it, first run salad-bar/wizard.py

You can override the mocking methods for any property on a type, or more generally for a Avro type
like int, bool, str.

In test.py we override lat and lon in geolocation from normal floats to be more realistic values that should be mappable.


