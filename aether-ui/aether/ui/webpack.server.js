
const fs = require('fs')
const webpack = require('webpack')
const WebpackDevServer = require('webpack-dev-server')
const buildConfig = require('./webpack.common')

const WEBPACK_URL = 'http://localhost:3000'

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
  //    Access to XXX at 'https://localhost:3000/static/ZZZ' from origin
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
  .listen(3000, '0.0.0.0', () => {
    console.log('Listening at', WEBPACK_URL)
  })
