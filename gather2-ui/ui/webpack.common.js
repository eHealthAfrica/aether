var path = require('path')

var BundleTracker = require('webpack-bundle-tracker')
var ExtractTextPlugin = require('extract-text-webpack-plugin')
var webpack = require('webpack')

function getApps (hmr) {
  var list = {
    // the apps that DO NOT need Hot Module Replacement in development mode
    'common': [ 'jquery', 'tether', 'bootstrap' ],
    'html5shiv': 'html5shiv'
  }

  // The list of current apps that DO need Hot Module Replacement in development mode
  var apps = [
    {
      name: 'styles',
      path: './assets/css/index.scss'
    },
    {
      name: 'surveys',
      path: './assets/apps/surveys'
    },
    {
      name: 'surveyors',
      path: './assets/apps/surveyors'
    }
  ]

  apps.forEach(app => {
    list[app.name] = (hmr ? hmr.concat([app.path]) : app.path)
  })

  return list
}

var stylesAsJsRules = [
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

var stylesAsCssRules = [
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

module.exports = function (custom) {
  return {
    context: __dirname,

    entry: getApps(custom.entry),

    module: {
      rules: [
        // to transform JSX into JS
        {
          test: /\.jsx?$/,
          exclude: /node_modules/,
          use: [
            { loader: 'react-hot-loader/webpack' },
            {
              loader: 'babel-loader',
              options: {
                presets: ['es2015', 'react', 'stage-2']
              }
            }
          ]
        },
        // font files
        {
          test: /\.woff(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'url-loader',
          options: {
            limit: 10000,
            mimetype: 'application/font-woff'
          }
        },
        {
          test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'url-loader',
          options: {
            limit: 10000,
            mimetype: 'application/font-woff'
          }
        },
        {
          test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'url-loader',
          options: {
            limit: 10000,
            mimetype: 'application/octet-stream'
          }
        },
        {
          test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'url-loader',
          options: {
            limit: 10000,
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
            limit: 10000,
            mimetype: 'image/png'
          }
        },

        // JSON
        {
          test: /\.json$/,
          loader: 'json-loader'
        }
      ].concat((custom.stylesAsCss ? stylesAsCssRules : stylesAsJsRules))
    },

    output: Object.assign({
      filename: '[name]-[hash].js',
      library: ['gather2', '[name]'],
      libraryTarget: 'var',
      path: path.resolve(__dirname, './assets/bundles')
    }, custom.output),

    plugins: [
      new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
        Tether: 'tether'
      }),

      new BundleTracker({
        path: __dirname,
        filename: './assets/bundles/webpack-stats.json'
      }),

      new webpack.EnvironmentPlugin(['GATHER_ORG_NAME']),
      new webpack.DefinePlugin({
        'process.env': {
          'NODE_ENV': JSON.stringify(custom.production ? 'production' : 'development')
        }
      })
    ].concat(custom.plugins),

    resolve: {
      modules: ['node_modules'],
      extensions: ['.js', '.jsx']
    }
  }
}
