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

import json
import jwt
import os
import requests

from flask import Flask, jsonify, request, render_template, send_from_directory
from jwcrypto.jwk import JWK
from keycloak import KeycloakAdmin

from settings import (
    APP_PORT,
    HOST,
    JWT_COOKIE,
    REALM_COOKIE,

    KEYCLOAK_URL,
    KC_URL,
    KC_ADMIN_USER,
    KC_ADMIN_PASSWORD,
    KC_MASTER_REALM,
)


APP_RENDER_KWARGS = {
    'host': HOST,
    'jwt_cookie': JWT_COOKIE,
    'realm_cookie': REALM_COOKIE,
}
KEYCLOAK_OIDCS = {}
PUBLIC_KEYS = {}

app = Flask(__name__, template_folder='templates')

app.logger.info(f'Authorization Setup with Keycloak on {KC_URL}!')


def get_kc_admin_token():
    keycloak_admin = KeycloakAdmin(server_url=KC_URL,
                                   username=KC_ADMIN_USER,
                                   password=KC_ADMIN_PASSWORD,
                                   realm_name=KC_MASTER_REALM,
                                   verify=True)
    token = keycloak_admin.token['access_token']
    headers = {
        'authorization': f'Bearer {token}',
    }
    return headers


def get_realms():
    headers = get_kc_admin_token()
    url = f'{KC_URL}admin/realms'
    res = requests.get(url, headers=headers)
    realms = res.json()
    return {
        r.get('id'): r.get('realm')
        for r in realms
        if r.get('id') != 'master'
    }


def get_oidc(realm):
    realm_client = f'{realm}-oidc'
    headers = get_kc_admin_token()
    INSTALLATION_URL = (
        f'{KC_URL}admin/realms/{realm}/clients/{realm_client}'
        '/installation/providers/keycloak-oidc-keycloak-json'
    )
    res = requests.get(INSTALLATION_URL, headers=headers)
    oidc = res.json()
    oidc['auth-server-url'] = KEYCLOAK_URL
    return oidc


def get_public_key(realm):
    CERT_URL = f'{KC_URL}realms/{realm}/protocol/openid-connect/certs'
    res = requests.get(CERT_URL)
    res.raise_for_status()
    jwk_key = res.json()['keys'][0]
    key_obj = JWK(**jwk_key)
    RSA_PUB_KEY = str(key_obj.export_to_pem(), 'utf-8')
    return RSA_PUB_KEY


def setup_auth():
    realms = get_realms()
    for _id, realm in realms.items():
        KEYCLOAK_OIDCS[realm] = get_oidc(realm)
        PUBLIC_KEYS[realm] = get_public_key(realm)
    return [KEYCLOAK_OIDCS, PUBLIC_KEYS]


def validate_token(tenant, headers=None, cookies=None):
    if not cookies:
        cookies = {}
    if not headers:
        headers = {}
    if tenant not in PUBLIC_KEYS:
        PUBLIC_KEYS[tenant] = get_public_key(tenant)
    header_auth = headers.get('authorization')
    if header_auth:
        raw = header_auth[7:]
    else:
        raw = cookies.get(JWT_COOKIE)

    return jwt.decode(raw, PUBLIC_KEYS[tenant], audience='account', algorithms='RS256')


## Protected Service

@app.route('/auth/user/<tenant>/token')
def demo(tenant):
    try:
        token = validate_token(tenant, request.headers, request.cookies)
    except jwt.exceptions.InvalidSignatureError:
        return app.response_class(response=json.dumps({'error': 'invalid_signature_for_realm'}),
                                  status=401,
                                  mimetype='application/json')
    except jwt.exceptions.ExpiredSignatureError:
        return app.response_class(response=json.dumps({'error': 'signature_expired'}),
                                  status=401,
                                  mimetype='application/json')
    except requests.exceptions.HTTPError:
        return app.response_class(response=json.dumps({'error': 'invalid_realm'}),
                                  status=401,
                                  mimetype='application/json')
    return render_template('./token.html', token=json.dumps(token,indent=2))


# Works for refreshing via UI
@app.route('/auth/user/<tenant>/refresh')
def refresh(tenant):
    redirect = request.args.get('redirect', None) or f'{HOST}/auth/user/{tenant}/token'
    return render_template('./index.html', tenant=tenant, redirect=redirect, **APP_RENDER_KWARGS)


# Logout
@app.route('/auth/user/<tenant>/logout')
def logout(tenant):
    redirect = request.args.get('redirect', None) or f'{HOST}/auth/login/{tenant}'
    return render_template('./logout.html', tenant=tenant, redirect=redirect, **APP_RENDER_KWARGS)


## PUBLIC

## Static Assets
@app.route('/auth/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


# Base route returns an error
@app.route('/auth/')
@app.route('/auth/login/')
def base():
    if 'realm' not in request.args:
        return render_template('./realm.html')

    realm = request.args.get('realm')
    redirect = request.args.get('redirect', None) or f'{HOST}/auth/user/{realm}/token'
    return render_template('./index.html', tenant=realm, redirect=redirect, **APP_RENDER_KWARGS)


# Login Route
@app.route('/auth/login/<tenant>')
def login(tenant=None):
    if not tenant:
        return jsonify({'error': 'a realm must be specified for login /auth/login/{realm}'})

    redirect = request.args.get('redirect', None) or f'{HOST}/auth/user/{tenant}/token'
    return render_template('./index.html', tenant=tenant, redirect=redirect, **APP_RENDER_KWARGS)


# Public Information
@app.route('/auth/login/<tenant>/keycloak.json')
def kc_json(tenant):
    if tenant not in KEYCLOAK_OIDCS:
        KEYCLOAK_OIDCS[tenant] = get_oidc(tenant)
    return jsonify(KEYCLOAK_OIDCS[tenant])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)
