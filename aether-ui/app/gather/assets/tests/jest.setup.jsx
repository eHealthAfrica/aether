import { JSDOM } from 'jsdom'
import fetch from 'node-fetch'

global.navigator = { userAgent: 'node.js', platform: 'Chrome' }
global.document = new JSDOM('<!doctype html><html><body></body></html>')
global.window = global.document.window
global.window.fetch = fetch
global.FormData = global.window.FormData
