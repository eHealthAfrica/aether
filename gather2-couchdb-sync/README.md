Gather2 CouchDB Sync
==========

Let's mobile clients sync to CouchDB. This server posts from CouchDB to Gather 2.

Setup
----

- You'll need the `GOOGLE_CLIENT_ID` from lastpass. The client secret is not needed.
- You need to generate a `GATHER_CORE_TOKEN` in your Gather Core admin interface.
- To run with HAT-Microsensus you need to make sure the 'village' and 'building' surveys have been created in your Gather Core instance (the 'name' should be exactly like the document prefixes from the HAT-Microcensus mobile app).

Components
----

### Credentials Exchange

The endpoint `/sync/signin` is set up for the mobile devices to exchange their google identity token for a set of couchdb credentials.

#### POST /sync/signin

```
{ idToken: [GOOGLE JWT], deviceId: [mobile device id, string] }
```

returns

```
{ username: string, password: string, db: string, url: string }
```

In order for a mobile client to gain access, it needs to send a token from a valid email account. In the admin interface, `http://localhost:8666/admin`, you can set valid email addresses under **MobileUser**. **DeviceDB** is handled by the backend and should usually not be touched.

### RQ Import Task

The import task is ran as an RQ scheduled job, the interval is defined in `importer/apps.py`. The importer writes its results to the logs, and it also writes meta documents for each imported/errored document. If the main document is `village-aaabbb` the meta document will be written under `village-aaabbb-synced`. This will contain any error messages from importing as well.

**Dev note** when working on the the RQ Task, the container needs to be restarted manually for changes to take effect :(

#### Retreiving Import Errors

Every user database have a design doc `sync/errors` that can be used to look for import errors under `[COUCH_URL]/[DB_NAME]/_design/sync/_view/errors`

#### Matching Surveys and Responses

Right now surveys are matched on the `name` key in Gather, and the `doc._id` prefix. To run with hat microsurveys, the **village** schema needs to be posted with the name **village** and the **building** schema needs to be posted with that name. Otherwise, those documents won't be imported.

#### Re-trying imports

When going to the admin interface, find a model called DeviceDB. Under the DeviceDB object, reset **last synced seq** to 0. This will make the next import run retry all the documents. Documents that have been successfully imported will not be re-imported.

#### Re-running all imports including the ones that got imported already.
If this is the effect you want, you'll need to delete all the `-synced` documents. You probably wanna write a CouchDB view for this, and then script deleting all the documents.

#### Run the import task manually
The import task can be run manually in development with: `docker-compose run couchdb-sync manage rqenqueue "importer.tasks.import_synced_devices_task"`

Testing sync locally
----

1. Run this repository with `docker-compose up`. You'll need to define the following env vars for sync (see docker-compose.yml): `GOOGLE_CLIENT_ID` and `GATHER_CORE_TOKEN`. The Gather Core token is created inside the Admin interface of your local gather core instance. The Google Client Id can be found in Lastpass or created in [https://console.developers.google.com/apis/credentials?project=hat-microsurveys&organizationId=883350201643](Google API Dev Console). If you create one, you need a Web Application Client for the Google+ Api.

2. Inside the local admin, set up a MobileUser for the email-address you're gonna use.

3. Run/build HAT-Microsurveys. If running in the browser, you'll need to setup `GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and HAT_GATHER_SERVER_URL`. The URL should be pointing to *the nginx instance in docker-compose (port 8667), not couchdb-sync*. If running on mobile, you need `GOOGLE_CLIENT_ID, and HAT_GATHER_SERVER_URL`. Use the same key as in 1, it should be a Web Application key, **not** a Mobile Application key.

Running tests
-----

To test Gather import, you need to generate a Gather API key in the gather core interface and set the `GATHER_CORE_TOKEN` and `GATHER_CORE_URL` environment variables.

Run all tests with:

`docker-compose run couchdb-sync manage test`

You can run separate tests using (for example):

`docker-compose run couchdb-sync manage test importer.tests.test_import`

Everything about the Google Tokens
-------

- Go to [https://console.developers.google.com/apis/credentials](Google Developer Console) and create a project.

- Under **Create Credentials** you have a few different options. You need API keys (good to have different for dev/prod) and OAuth Client IDS.
- Here's the tricky part, the API keys should be for **Web Application**. The Oauth Client Ids should be for **Android**.

- Anywhere you use a GOOGLE_CLIENT ID it should always be the **Web Application** one. The **Android** is **never to be used but it needs to be there**

- When you do the **Android** you need to hash the signing certificate for the App. You need one for debug key and one for release key. Run `keytool -exportcert -list -v -alias release -keystore ./android.release.keystore` (you need to decrypt the release keystore first) and submit the resulting **SHA-1** hash.
