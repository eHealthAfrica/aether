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
   The URL should be pointing to http://sync.aether.local.
   If running on mobile, you need `GOOGLE_CLIENT_ID` and `AETHER_COUCHDB_SYNC_URL`.
   Use the same key as in 1, it should be a Web Application key, **not** a Mobile Application key.

## Step by step guide to testing locally with Gather DRC (Microcensus App)

This guide assumes that you want to run Gather DRC on an Android device and Gather on your local development machine. You'll need to have the Gather and Aether repos, with a working `.env` files in the `gather` directory. We're going to submit a POI ("village") from the app and have it created as an entity in Kernel. You will also need the Gather DRC repo, and the requisite Android SDK and build tools installed.

1. You will need a domain name that can be resolved by the Android device. One way to do this is with [Ngrok](https://ngrok.com/):
```
> ngrok http 80
ngrok by @inconshreveable                                      (Ctrl+C to quit)

Session Status                online
Session Expires               7 hours, 59 minutes
Update                        update available (version 2.2.8, Ctrl-U to update
Version                       2.1.18
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    http://502deefa.ngrok.io -> localhost:80
Forwarding                    https://502deefa.ngrok.io -> localhost:80
```
Make a note of the domain name that has been assigned to you (in this case `502deefa.ngrok.io`)

2. Make a build of Gather DRC that submits to this URL:
```
KEYSTORE_PASS=[keystore pass] AETHER_COUCHDB_SYNC_URL=https://502deefa.ngrok.io GOOGLE_CLIENT_ID=[google client id] NODE_ENV=production LOCALE=fr npm run build-release
```
The values for `KEYSTORE_PASS` and `GOOGLE_CLIENT_ID` are in Lastpass (`Shared-Microcensus-DRC > Keystore pass and Google client ID`).

3. Configure the CouchDB Sync Nginx to work with this URL. Edit `gather/local-setup/nginx/sites-enabled/sync.conf`, so that the `server_name` matches your Ngrok URL:
```
server {
  listen                    80;
  charset                   utf-8;
  server_name               502deefa.ngrok.io;
  client_max_body_size      75M;
  ...
```

4. Add the Google Client ID to your `.env` file as the value for `COUCHDB_SYNC_GOOGLE_CLIENT_ID` in the `Aether CouchDB-Sync Module` section

5. Start up Gather:
```
docker-compose -f docker-compose-local.yml up
```

6. Go the CouchDB Sync module and create the necessary artefacts in the [admin](http://sync.aether.local/admin/sync/). You will need to create a `Project`, and a `Schema` called `village` that is associated with that project. The Avro schema for a village can be found in the `hat-microcensus` repo: `hat-microcensus/src/schemas/village.avsc`.

7. Propagate the artefacts to Kernel. In the projects list, select your new project and choose _Propagate selected projects to Aether Kernel_ from the _Action_ dropdown. Press _Go_.

8. Add the email Google user of your Android device as a `Mobile user`. (You can also do this from the Gather UI by creating a new `Sync User`.)

9. Install the app on your Android device using `adb install`. Create a new village by pressing the big `+` button, then sync the data by pressing the `...` button in the top right hand corner.

10. Verify that the data has been replicated to CouchDB on your local machine by going to `https://104b04df.ngrok.io/_couchdb/_utils` (or `http://localhost:5984/_utils`).

11. Now you need to wait for RQ to pick up the village and submit it to Kernel. If you don't feel like waiting, you can go to [http://sync.aether.local/rq/queues/0/finished/](http://sync.aether.local/rq/queues/0/finished/), click on the queue, then press the _Enqueue_ button at the bottom.

12. Your village should now have been submitted to Kernel, and extracted into an Entity. If you go to Gather, you should also see the `village` Survey with one row in the table.

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
