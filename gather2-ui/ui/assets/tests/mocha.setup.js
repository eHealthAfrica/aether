const babelRegister = require('babel-register')
const jsdom = require('jsdom')
const { JSDOM } = jsdom

babelRegister({
  presets: ['es2015', 'react', 'stage-2'],
  extensions: ['.jsx']
})

global.navigator = {userAgent: 'node.js', platform: 'Chrome'}

global.document = new JSDOM('<!doctype html><html><body></body></html>')
global.window = global.document.window
global.window.fetch = require('node-fetch')
global.FormData = global.window.FormData
