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

const express = require('express')
const http = require('http')
const path = require('path')
const webpack = require('webpack')
const buildConfig = require('./webpack.common')

const WEBPACK_PORT = 3004
const WEBPACK_URL = 'http://aether.local'
const WEBPACK_HMR_PATH = '/ui-assets/__webpack_hmr'

const HMR_URL = 'webpack-hot-middleware/client?' +
  '&path=' + WEBPACK_URL + WEBPACK_HMR_PATH +
  '&timeout=20000' +
  '&reload=true'

const webpackOptions = Object.assign(
  {},
  buildConfig({
    production: false,
    stylesAsCss: false,

    hmr: HMR_URL,

    output: {
      // Tell django to use this URL to load packages
      // and not use STATIC_URL + bundle_name
      publicPath: WEBPACK_URL + '/ui-assets/static/'
    },

    plugins: [
      // enable HMR globally
      new webpack.HotModuleReplacementPlugin()
    ]
  }),
  {
    devtool: 'inline-source-map'
  }
)

const serverOptions = {
  publicPath: webpackOptions.output.publicPath,
  contentBase: path.resolve(__dirname, '../'),
  host: '0.0.0.0',

  inline: true,
  historyApiFallback: true,
  https: false,

  // It suppress error shown in console, so it has to be set to false.
  quiet: false,
  // It suppress everything except error, so it has to be set to false as well
  // to see success build.
  noInfo: false,
  stats: {
    // Config for minimal console.log mess.
    builtAt: true,
    assets: false,
    colors: true,
    version: false,
    hash: false,
    timings: false,
    chunks: false,
    chunkModules: false
  },

  watchOptions: {
    aggregateTimeout: 300,
    poll: 1000
  }
}

const app = express()

// Step 1: Create & configure a webpack compiler
var compiler = webpack(webpackOptions)

// Step 2: Attach the dev middleware to the compiler & the server
app.use(require('webpack-dev-middleware')(compiler, serverOptions))

// Step 3: Attach the hot middleware to the compiler & the server
app.use(require('webpack-hot-middleware')(compiler, {
  log: console.log,
  path: WEBPACK_HMR_PATH,
  heartbeat: 10 * 1000
}))

app.get('/', function (req, res) {
  res.send(webpackOptions)
})

// Step 4: Start the server
var server = http.createServer(app)
server.listen(WEBPACK_PORT, '0.0.0.0', () => {
  console.log('Listening on %j', server.address())
})
