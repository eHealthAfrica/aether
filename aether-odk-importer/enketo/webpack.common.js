var path = require('path')

var BundleTracker = require('webpack-bundle-tracker')
var ExtractTextPlugin = require('extract-text-webpack-plugin')
var webpack = require('webpack')

function getApps (hmr) {
  var list = {
    // the apps that DO NOT need Hot Module Replacement in development mode
    // 'common': [ 'jquery', 'bootstrap' ],
    // 'html5shiv': 'html5shiv'
  }

  // The list of current apps that DO need Hot Module Replacement in development mode
  var apps = [
    {
      name: 'styles',
      path: './assets/css/index.scss'
    },
  ]

  apps.forEach(app => {
    list[app.name] = (hmr ? hmr.concat([app.path]) : app.path)
  })

  return list
}

module.exports = function (custom) {
  return {
    context: __dirname,

    entry: getApps(custom.entry),

    module: {
      rules: [
        // to transform es2015 into JS
        // {
        //   test: /\.js?$/,
        //   exclude: /node_modules/,
        //   use: [
        //     { loader: 'react-hot-loader/webpack' },
        //     {
        //       loader: 'babel-loader',
        //       options: {
        //         presets: ['es2015', 'stage-2']
        //       }
        //     }
        //   ]
        // },
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
    },

    output: Object.assign({
      filename: '[name]-[hash].js',
      library: ['aether', '[name]'],
      libraryTarget: 'var',
      path: path.resolve(__dirname, './assets/bundles')
    }, custom.output),

    plugins: [
      new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery'
      }),

      new BundleTracker({
        path: __dirname,
        filename: './assets/bundles/webpack-stats.json'
      }),

      new webpack.EnvironmentPlugin(['AETHER_ORG_NAME', 'AETHER_MODULES']),
      new webpack.DefinePlugin({
        'process.env': {
          'NODE_ENV': JSON.stringify(custom.production ? 'production' : 'development')
        }
      })
    ].concat(custom.plugins),

    resolve: {
      modules: ['node_modules'],
      extensions: ['.js']
    }
  }
}
