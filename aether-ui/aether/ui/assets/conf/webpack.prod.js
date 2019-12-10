/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

var fs = require('fs')
var buildConfig = require('./webpack.common')

function readFile (filename) {
  try {
    return fs.readFileSync(filename).toString().replace(/(\r\n|\n|\r)/gm, '')
  } catch (e) {
    return null
  }
}

// read VERSION and REVISION files
// to identify files with current branch and commit hash
var version = readFile('/var/tmp/VERSION')
var revision = readFile('/var/tmp/REVISION')

var prefix = `[name]-${version || '0.0.0'}`

module.exports = buildConfig({
  production: true,
  stylesAsCss: true,
  jsFilename: `${prefix}-${revision || '[hash]'}.js`,
  cssFilename: `${prefix}-${revision || '[chunkhash]'}.css`
})
