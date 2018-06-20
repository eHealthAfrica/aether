const path = require('path')
const BundleTracker = require('webpack-bundle-tracker')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const webpack = require('webpack')
const buildEntries = require('./webpack.apps')

module.exports = (custom) => ({
  mode: (custom.production ? 'production' : 'development'),
  context: __dirname,

  entry: buildEntries(custom.entryOptions),

  output: Object.assign({
    filename: '[name]-[hash].js',
    library: ['ui', '[name]'],
    libraryTarget: 'var',
    path: path.resolve(__dirname, './assets/bundles/')
  }, custom.output),

  optimization: {
    minimize: custom.production
  },

  module: {
    rules: [
      {
        test: /\.(css|sass|scss)$/,
        use: [
          // to transform styles into CSS or JS file
          { loader: (custom.stylesAsCss ? MiniCssExtractPlugin.loader : 'style-loader') },
          { loader: 'css-loader' },
          { loader: 'sass-loader' }
        ]
      },

      // to transform JSX into JS
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        options: {
          // This is a feature of `babel-loader` for Webpack (not Babel itself).
          // It enables caching results in ./node_modules/.cache/babel-loader/
          // directory for faster rebuilds.
          cacheDirectory: true
        }
      }
    ]
  },

  plugins: [
    // use to provide the global constants
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
      Popper: 'popper.js'
    }),

    // needed by `django-webpack-loader`
    new BundleTracker({
      path: __dirname,
      filename: './assets/bundles/webpack-stats.json'
    }),

    // Environment variables
    new webpack.DefinePlugin({
      'process.env': {
        'NODE_ENV': JSON.stringify(custom.production ? 'production' : 'development')
      }
    }),

    // extract styles as a CSS file not JS file
    ...(custom.stylesAsCss
      ? [new MiniCssExtractPlugin({ filename: '[name]-[chunkhash].css' })]
      : []
    ),

    ...(custom.plugins || [])
  ],

  resolve: {
    modules: ['node_modules'],
    extensions: ['.js', '.jsx']
  }
})
