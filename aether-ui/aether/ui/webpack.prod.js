var buildConfig = require('./webpack.common')

module.exports = buildConfig({
  production: true,
  stylesAsCss: true
})
