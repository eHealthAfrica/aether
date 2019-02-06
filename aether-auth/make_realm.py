import json
import os
from jwcrypto.jwk import JWK
from keycloak import KeycloakAdmin
import requests


# Keycloak Information
HOST_URL = 'aether.local'
KC_INT_HOST = 'keycloak:8080'
INTERNAL_KC = f'http://{KC_INT_HOST}/keycloak/auth/'  # external url
KEYCLOAK_URL = f'http://{HOST_URL}/keycloak/auth/'  # external url

KC_MASTER_REALM = 'master'
KC_ADMIN_USER = 'admin'  # Admin on MASTER realm
KC_ADMIN_PASSWORD = 'password'

# Kong Information
KONG_HOST = 'kong'  # usually an internal reference as Kong admin is not public
KONG_URL = f'http://{KONG_HOST}:8001/'
CONSUMERS_URL = f'{KONG_URL}consumers'

REALMS_PATH = '/code/realm'

# Get administrative Token with KC Master Credentials

def make_realm(name, config):
    CERT_URL = f'{INTERNAL_KC}realms/{name}/protocol/openid-connect/certs'
    print(f'Creating realm: {name}')
    keycloak_admin = KeycloakAdmin(server_url=INTERNAL_KC,
                                   username=KC_ADMIN_USER,
                                   password=KC_ADMIN_PASSWORD,
                                   realm_name=KC_MASTER_REALM,
                                   verify=False)

    token = keycloak_admin.token['access_token']

    # Register realm with provided config

    realm_url = f'{INTERNAL_KC}admin/realms'
    headers = {
        'content-type': 'application/json',
        'authorization': f'Bearer {token}'
        } 
    res = requests.post(realm_url, headers=headers, data=json.dumps(config))
    if not res.status_code is 201:
        print(res, res.text)
        raise ValueError('Could not create realm.')

    # Make a Single Kong Consumer for JWT covering the whole realm.

    data = {
        'username': f'{name}-jwt-consumer'
    }
    res = requests.post(
        CONSUMERS_URL,
        data=data
        )
    details = res.json()
    consumer_id = details['id']
    print(consumer_id)
    # Get the public key from Keycloak

    res = requests.get(
            CERT_URL
        )
    jwk_key = res.json()['keys'][0]

    # Transform JWK into a PEM.

    key_obj = JWK(**jwk_key)
    RSA_PUB_KEY = str(key_obj.export_to_pem(), 'utf-8')

    # Add JWT public key to Kong Consumer

    CONSUMER_CREDENTIALS_URL = f'{CONSUMERS_URL}/{consumer_id}/jwt'
    data = {
        'key': f'{KEYCLOAK_URL}realms/{name}',
        'algorithm': 'RS256',
        'rsa_public_key': RSA_PUB_KEY
    }
    res =requests.post(CONSUMER_CREDENTIALS_URL,
            data=data
        )

    print(f'Realm: {name} created on keycloak: {KEYCLOAK_URL}')


def find_available_realms():
    realms = {}
    _files = os.listdir(REALMS_PATH)
    for f in _files:
        name = f.split('.json')[0]
        with open(f'{REALMS_PATH}/{f}') as _f:
            config = json.load(_f)
            realms[name] = config
    return realms
            


if __name__ == "__main__":
    realms = find_available_realms()
    for name, config in realms.items():
        make_realm(name, config) 