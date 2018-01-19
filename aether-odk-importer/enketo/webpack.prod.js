var webpack = require('webpack')
var ExtractTextPlugin = require('extract-text-webpack-plugin')

var buildConfig = require('./webpack.common')

module.exports = buildConfig({
  production: true,
  stylesAsCss: true,

  plugins: [
    // minifies your code
    new webpack.optimize.UglifyJsPlugin({
      compressor: {
        warnings: false
      }
    }),

    // extract styles in a css file
    new ExtractTextPlugin('[name]-[chunkhash].css')
  ]
})
