import json
import requests


# Kong info

# TODO Make ENVs

HOST = 'aether.local'  # External URL for host
KONG_URL = 'http://kong:8001/'
CLIENT_URL = 'http://auth:3011/'
CLIENT_NAME = 'auth' 
PLUGIN_URL = f'{KONG_URL}services/{CLIENT_NAME}/plugins'

print(f'Exposing Service {CLIENT_NAME} @ {CLIENT_URL}')

# Register Client with Kong

# Single API Service

data = {
    'name':f'{CLIENT_NAME}',
    'url': f'{CLIENT_URL}'
}

res = requests.post(
        f'{KONG_URL}services/',
        data=data
    )
api_details = res.json()
api_id = api_details['id']

# routes

ROUTE_URL = f'{KONG_URL}services/{CLIENT_NAME}/routes'

# open Route

# EVERYTHING past /login will be public
data = {
    'paths' : [
        f'/{CLIENT_NAME}/login'
    ],
    'strip_path': 'false'
}

res = requests.post(
    ROUTE_URL,
    data=data
    )

route_info = res.json()

# protected Routes

# EVERYTHING past /api will be JWT controlled

data = {
    'paths' : [
        f'/{CLIENT_NAME}/user'
    ],
    'strip_path': 'false'
}

res = requests.post(
    ROUTE_URL,
    data=data
    )

route_info = res.json()
protected_route_id = route_info['id']

# Add JWT Plugin to protected route.

ROUTE_URL = f'{KONG_URL}routes/{protected_route_id}/plugins'

data = {
    'name': 'jwt',
    'config.cookie_names' : ['aether-jwt']
}

res = requests.post(
        ROUTE_URL,
        data=data
    )

# ADD CORS Plugin to Kong for all localhost requests

data = {
    'name': 'cors',
    'config.origins': f'http://{HOST}/*',
    'config.methods': 'GET, POST',
    'config.headers': 'Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, Authorization',
    'config.exposed_headers': 'Authorization',
    'config.max_age': 3600,
    'config.credentials': 'true'
}

res = requests.post(PLUGIN_URL, data=data)
print(f'Service {CLIENT_NAME} from, {CLIENT_URL}' 
    + f' now being served by kong @ /{CLIENT_NAME}.')
