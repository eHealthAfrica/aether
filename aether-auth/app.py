# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import base64
from flask import Flask, jsonify, request, render_template, redirect
from jwcrypto.jwk import JWK
import jwt
from jwt.contrib.algorithms.pycrypto import RSAAlgorithm
import json
from keycloak import KeycloakAdmin
import requests
import os

ENV = lambda x : os.environ.get(x)

HOST = ENV('BASE_HOST')  # External URL for host

KC_URL = f'http://{ENV("KEYCLOAK_INTERNAL")}/keycloak/auth/'  # internal
KEYCLOAK_EXTERNAL = f'http://{HOST}/keycloak/auth/'
KC_ADMIN = ENV('KEYCLOAK_GLOBAL_ADMIN')
KC_PASSWORD = ENV('KEYCLOAK_GLOBAL_PASSWORD')
KC_MASTER_REALM = 'master'

app = Flask(__name__, template_folder='templates')

kcj = {}
PK = {}

def get_kc_admin_token():
    keycloak_admin = KeycloakAdmin(server_url=KC_URL,
                                   username=KC_ADMIN,
                                   password=KC_PASSWORD,
                                   realm_name=KC_MASTER_REALM,
                                   verify=True)
    token = keycloak_admin.token['access_token']
    headers = {
        'authorization': f'Bearer {token}'
    }
    return headers

def get_realms():
    headers = get_kc_admin_token()
    url = f'{KC_URL}admin/realms'
    res = requests.get(url, headers=headers)
    realms = res.json()
    return {r.get('id'): r.get('realm') for r in realms if r.get('id') != 'master'}
    

def get_oidc(kc_url, realm):
    realm_client = f'{realm}-oidc'
    headers = get_kc_admin_token()
    INSTALLATION_URL = f'{kc_url}admin/realms/{realm}/clients/{realm_client}/installation/providers/keycloak-oidc-keycloak-json'
    res = requests.get(INSTALLATION_URL, headers=headers)
    oidc = res.json()
    oidc['auth-server-url'] = KEYCLOAK_EXTERNAL
    return oidc

def get_public_key(kc_url, realm):
    CERT_URL = f'{kc_url}realms/{realm}/protocol/openid-connect/certs'
    res = requests.get(
        CERT_URL
    )
    jwk_key = res.json()['keys'][0]
    key_obj = JWK(**jwk_key)
    RSA_PUB_KEY = str(key_obj.export_to_pem(), 'utf-8')
    return RSA_PUB_KEY

def setup_auth():
    global kcj, PK
    realms = get_realms()
    for _id, realm in realms.items():
        kcj[realm] = get_oidc(KC_URL, realm)
        PK[realm] = get_public_key(KC_URL, realm)
    return [kcj, PK]


def validate_token(tenant, headers=None, cookies=None):
    if not cookies: 
        cookies = {}
    if not headers:
        headers = {}
    if not tenant in PK:
        try:
            PK[tenant] = get_public_key(KC_URL, tenant)
        except Exception as e:
            raise e
    header_auth = headers.get('authorization')
    if header_auth:
        raw = header_auth[7:]
    else:
        raw = cookies.get('aether-jwt')
    
    return jwt.decode(raw, PK[tenant], audience='account', algorithms='RS256')


app.logger.info(f'Authorization Setup with Keycloak on {KC_URL}!')

## Protected Service

@app.route("/auth/user/<tenant>/token")
def demo(tenant):
    try:
        token = validate_token(tenant, request.headers, request.cookies)
    except jwt.ExpiredSignatureError:
        return app.response_class(response=json.dumps({'error': 'signature_expired'}),
                                  status=401,
                                  mimetype='application/json')
    return render_template('./token.html', token=json.dumps(token,indent=2))

# Works for refreshing via UI
@app.route("/auth/user/<tenant>/refresh")
def refresh(tenant):
    redirect = request.args.get('redirect', None) \
        or f'http://{HOST}/auth/user/{tenant}/token'
    return render_template('./index.html', tenant=tenant, redirect=redirect)

# Logout
@app.route("/auth/user/<tenant>/logout")
def logout(tenant):
    redirect = request.args.get('redirect', None) \
        or f'http://{HOST}/auth/login/{tenant}'
    return render_template('./logout.html', tenant=tenant, redirect=redirect)

## PUBLIC
# Base route returns an error
@app.route("/auth")
def base(tenant):
    return jsonify({'error': 'a realm must be specified for login "/auth/login/{realm}"'})

# Login Route
@app.route("/auth/login")
@app.route("/auth/login/<tenant>")
def login(tenant=None):
    redirect = request.args.get('redirect', None) \
        or f'http://{HOST}/auth/user/{tenant}/token'
    if not tenant:
        return jsonify({'error': 'a realm must be specified for login /auth/login/{realm}'})        
    return render_template('./index.html', tenant=tenant, redirect=redirect)

# Public Information
@app.route("/auth/login/<tenant>/keycloak.json")
def kc_json(tenant):
    if not tenant in kcj:
        try:
            kcj[tenant] = get_oidc(KC_URL, tenant)
        except Exception as e:
            raise e
    return jsonify(kcj[tenant])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3011)
