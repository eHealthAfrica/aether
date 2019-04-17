# Aether CouchDB Sync

Let's mobile clients sync to CouchDB. This server posts from CouchDB to Aether.

## Setup

You'll need the `GOOGLE_CLIENT_ID` environment variable, used to verify the
device identity with Google.
See more in https://developers.google.com/identity/protocols/OAuth2


## Components

### Credentials Exchange

The endpoint `/sync/signin` is set up for the mobile devices to exchange their
google identity token for a set of couchdb credentials.

#### POST /sync/signin

```json
{
    "idToken": [GOOGLE JWT],
    "deviceId": [mobile device id, string]
}
```

returns

```json
{
    "username": string,
    "password": string,
    "url": string,
    "db": string
}
```

In order for a mobile client to gain access, it needs to send a token from a
valid email account. In the admin interface, `/admin`,
you can set valid email addresses under **MobileUser**.
**DeviceDB** is handled by the backend and should usually not be touched.

### RQ Import Task

The import task is run as an RQ scheduled job, the interval is defined in
`aether/sync/apps.py`. The importer writes its results to the logs, and it also
writes meta documents for each imported/errored document.

If the main document is `village-aaabbb` the meta document will be written under
`village-aaabbb-synced`. This will contain any error messages from importing as well.

**Dev note** when working on the the RQ Task, the container needs to be
restarted manually for changes to take effect :(

#### Retrieving Import Errors

Every user database have a design doc `sync/errors` that can be used to look for
import errors under `[COUCH_URL]/[DB_NAME]/_design/sync/_view/errors`

#### Matching Schemas and Submissions

Right now schema documents are matched using the `name` prefix included in
the `_id` property.

```json
{
    "_id": "village-aaabbb",
    "rest_of_data": "...."
}
```

For each schema used in the Aether Mobile App there should be an entry in the
**Schema** model indicating the Aether Kernel artefact ID linked to it.
Otherwise, those documents won't be imported.

#### Re-trying imports

When going to the admin interface, find a model called `DeviceDB`.
Under the DeviceDB object, reset **last synced seq** to 0.
This will make the next import run retry all the documents.
Documents that have been successfully imported will not be re-imported.

#### Re-running all imports including the ones that got imported already.

If this is the effect you want, you'll need to delete all the `-synced` documents.
You probably wanna write a CouchDB view for this, and then script deleting all the documents.

#### Run the import task manually

The import task can be run manually in development with:

```bash
docker-compose run couchdb-sync manage rqenqueue "aether.sync.tasks.import_synced_devices_task"
```

## Testing sync locally

1. Run this repository with `docker-compose up`.
   You'll need to define the following env var for sync (see `docker-compose-base.yml`):
   `GOOGLE_CLIENT_ID`.
   The Google Client Id can be created in
   [https://console.developers.google.com/apis/credentials](Google API Dev Console).
   If you create one, you need a Web Application Client for the Google+Api.

2. Inside the local admin, set up a MobileUser for the email-address you're gonna use.

3. Run/build Aether Mobile App.
   If running in the browser, you'll need to setup `GOOGLE_CLIENT_ID`,
   `GOOGLE_CLIENT_SECRET` and `AETHER_COUCHDB_SYNC_URL`.
   The URL should be pointing to http://aether.local/sync/.
   If running on mobile, you need `GOOGLE_CLIENT_ID` and `AETHER_COUCHDB_SYNC_URL`.
   Use the same key as in 1, it should be a Web Application key, **not** a Mobile Application key.


## Everything about the Google Tokens

- Go to [https://console.developers.google.com/apis/credentials](Google Developer Console)
  and create a project.

- Under **Create Credentials** you have a few different options.
  You need API keys (good to have different for dev/prod) and OAuth Client IDS.

- Here's the tricky part, the API keys should be for **Web Application**.
  The Oauth Client Ids should be for **Android**.

- Anywhere you use a GOOGLE_CLIENT ID it should always be the **Web Application** one.
  The **Android** is **never to be used but it needs to be there**

- When you do the **Android** you need to hash the signing certificate for the App.
  You need one for debug key and one for release key.
  Run `keytool -exportcert -list -v -alias release -keystore ./android.release.keystore`
  (you need to decrypt the release keystore first) and submit the resulting **SHA-1** hash.
