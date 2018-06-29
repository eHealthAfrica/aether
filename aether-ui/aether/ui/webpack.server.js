/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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



const webpack = require('webpack')
const WebpackDevServer = require('webpack-dev-server')
const buildConfig = require('./webpack.common')

const WEBPACK_PORT = 3004
const WEBPACK_URL = `http://localhost:${WEBPACK_PORT}`

const config = buildConfig({
  production: false,
  stylesAsCss: false,

  entryOptions: [
    // bundle the client for webpack-dev-server
    // and connect to the provided endpoint
    'webpack-dev-server/client?' + WEBPACK_URL,
    // bundle the client for hot reloading
    // only- means to only hot reload for successful updates
    'webpack/hot/only-dev-server'
    // the entry point of our app
    // ...
  ],

  output: {
    // Tell django to use this URL to load packages
    // and not use STATIC_URL + bundle_name
    publicPath: WEBPACK_URL + '/static/'
  },

  plugins: [
    // enable HMR globally
    new webpack.HotModuleReplacementPlugin(),
    // prints more readable module names in the browser console on HMR updates
    new webpack.NamedModulesPlugin(),
    // do not reload if there is an error
    new webpack.NoEmitOnErrorsPlugin()
  ]
})

new WebpackDevServer(webpack(config), {
  publicPath: config.output.publicPath,
  hot: true,
  inline: true,
  historyApiFallback: true,
  // Fixes:
  //    Access to XXX at 'https://localhost:{port}/static/ZZZ' from origin
  //    has been blocked by CORS policy
  headers: { 'Access-Control-Allow-Origin': '*' },
  https: false,
  // It suppress error shown in console, so it has to be set to false.
  quiet: false,
  // It suppress everything except error, so it has to be set to false as well
  // to see success build.
  noInfo: false,
  stats: {
    // Config for minimal console.log mess.
    assets: false,
    colors: true,
    version: false,
    hash: false,
    timings: false,
    chunks: false,
    chunkModules: false
  }
})
  .listen(WEBPACK_PORT, '0.0.0.0', () => {
    console.log('Listening at', WEBPACK_URL)
  })
