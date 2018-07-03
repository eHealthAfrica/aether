#!/bin/bash
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
set -Eeuox pipefail


# Define help message
show_help() {
  echo """
  Commands
  ----------------------------------------------------------------------------
  bash          : run bash
  eval          : eval shell command

  test          : run ALL tests
  test_lint     : run standardjs and sass lint tests
  test_js       : run js tests with enzyme and jest

  build         : create distributed app
  start_dev     : start webpack server (only in DEV mode)
  """
}

test_lint() {
  npm run test-lint
}

test_js() {
  npm run test-js "${@:1}"
}


case "$1" in
  bash)
    bash
  ;;

  eval)
    eval "${@:2}"
  ;;

  test)
    test_lint
    test_js
    npm run webpack
  ;;

  test_lint)
    test_lint
  ;;

  test_js)
    test_js "${@:2}"
  ;;

  build)
    npm run webpack
  ;;

  start_dev)
    npm run webpack-server
  ;;

  help)
    show_help
  ;;

  *)
    show_help
  ;;
esac
