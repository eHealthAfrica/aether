/**
 * Taken from:
 *    https://facebook.github.io/jest/docs/en/configuration.html#testenvironment-string
 */

const JSDOMEnvironment = require('jest-environment-jsdom')
const fetch = require('node-fetch')
const testURL = 'http://localhost'

class UiTestsEnvironment extends JSDOMEnvironment {
  async setup () {
    await super.setup()

    // Issue that solves in tests: change window.location
    // https://github.com/jsdom/jsdom#reconfiguring-the-jsdom-with-reconfiguresettings
    this.global.jsdom = this.dom
    this.global.jsdom.reconfigure({ url: testURL })

    // used to create random data
    // https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/Array/from
    this.global.range = (start, end) => Array.from({length: end - start}, (v, i) => i + start)

    // uses "node-fetch" in tests, "whatwg-fetch" only works in browsers
    // check that the url is not an relative url, otherwise include it
    // Fixes: [TypeError: Only absolute URLs are supported]
    this.global.window.fetch = (url, opts) => (
      fetch(url.indexOf('/') === 0 ? testURL + url : url, opts)
    )
  }

  async teardown () {
    this.global.jsdom = null
    this.global.range = null
    this.global.window.fetch = null

    await super.teardown()
  }

  runScript (script) {
    return super.runScript(script)
  }
}

module.exports = UiTestsEnvironment
