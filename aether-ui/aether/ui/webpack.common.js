const path = require('path')
const BundleTracker = require('webpack-bundle-tracker')
const ExtractTextPlugin = require('extract-text-webpack-plugin')
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
      // to transform styles into CSS or JS file
      ...(custom.stylesAsCss
        ? [
          {
            test: /\.css$/,
            loader: ExtractTextPlugin.extract({
              fallback: 'style-loader',
              use: 'css-loader'
            })
          },
          {
            test: /\.scss$/,
            loader: ExtractTextPlugin.extract({
              fallback: 'style-loader',
              use: [
                { loader: 'css-loader' },
                { loader: 'sass-loader' }
              ]
            })
          }
        ]
        : [
          {
            test: /\.css$/,
            use: [
              { loader: 'style-loader' },
              { loader: 'css-loader' }
            ]
          },
          {
            test: /\.scss$/,
            use: [
              { loader: 'style-loader' },
              { loader: 'css-loader' },
              { loader: 'sass-loader' }
            ]
          }
        ]
      ),

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
      },

      // font files
      {
        test: /\.woff(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url-loader',
        options: {
          limit: 8192,
          mimetype: 'application/font-woff'
        }
      },
      {
        test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url-loader',
        options: {
          limit: 8192,
          mimetype: 'application/font-woff'
        }
      },
      {
        test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url-loader',
        options: {
          limit: 8192,
          mimetype: 'application/octet-stream'
        }
      },
      {
        test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url-loader',
        options: {
          limit: 8192,
          mimetype: 'image/svg+xml'
        }
      },
      {
        test: /\.eot(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'file-loader'
      },

      // images
      {
        test: /\.png(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url-loader',
        options: {
          limit: 8192,
          mimetype: 'image/png'
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
    new webpack.EnvironmentPlugin({
      AETHER_MODULES: 'kernel',
      CSV_HEADER_RULES: '',
      CSV_HEADER_RULES_SEP: ':'
    }),

    // extract styles as a CSS file not JS file
    ...(custom.stylesAsCss ? [new ExtractTextPlugin('[name]-[chunkhash].css')] : []),

    ...(custom.plugins || [])
  ],

  resolve: {
    modules: ['node_modules'],
    extensions: ['.js', '.jsx']
  }
})
