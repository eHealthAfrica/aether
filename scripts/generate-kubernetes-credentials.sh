#!/usr/bin/env bash
#
# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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
#

# This script can be used to generate a secrets.yaml file for local development
# with minikube
#
# Example:
# ./scripts/generate-kubernetes-credentials.sh > helm/test-secrets.yaml

# Generate a random alphanumeric string.
gen_pass () {
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
}

cat <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: secrets
type: Opaque
stringData:
  kernel-admin-password: $(gen_pass)
  kernel-database-user: postgres
  kernel-database-password: $(gen_pass)
  kernel-database-name: aether
  kernel-django-secret-key: $(gen_pass)
  kernel-token: $(gen_pass)
  odk-admin-password: $(gen_pass)
  odk-database-user: postgres
  odk-database-password: $(gen_pass)
  odk-database-name: odk
  odk-django-secret-key: $(gen_pass)
  odk-token: $(gen_pass)
EOF
