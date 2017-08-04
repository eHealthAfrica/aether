var webpack = require('webpack')
var ExtractTextPlugin = require('extract-text-webpack-plugin')

var buildConfig = require('./webpack.common')

module.exports = buildConfig({
  plugins: [
    // removes a lot of debugging code in React
    new webpack.DefinePlugin({
      'process.env': {
        'NODE_ENV': JSON.stringify('production')
      }
    }),

    // minifies your code
    new webpack.optimize.UglifyJsPlugin({
      compressor: {
        warnings: false
      }
    }),

    // extract styles in a css file
    new ExtractTextPlugin('[name]-[chunkhash].css')
  ],

  stylesAsCss: true
})
