/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/* global describe, it, expect, afterEach */

const nock = require('nock')

describe('test environment', () => {
  it('should set jsdom, range and window.fetch on its global object', () => {
    expect(global.jsdom).toBeTruthy()
    expect(global.range).toBeTruthy()
    expect(global.window.fetch).toBeTruthy()
  })

  it('should set the third party global variables', () => {
    expect(global.window.$).toBeTruthy()
    expect(global.window.jQuery).toBeTruthy()
    expect(global.window.Popper).toBeTruthy()
  })

  it('should set the default URL to http://localhost', () => {
    expect(window.location.href).toEqual('http://localhost/')
  })

  describe('global.range', () => {
    it('should create and array of ints', () => {
      expect(global.range(0, 0)).toEqual([])
      expect(global.range(0, 1)).toEqual([0])
      expect(global.range(1, 3)).toEqual([1, 2])
    })
  })

  describe('global.window.fetch', () => {
    afterEach(() => {
      nock.isDone()
      nock.cleanAll()
    })

    it('should include the testURL in the call with relative URLs', () => {
      nock('http://localhost').get('/foo').reply(200, { ok: true })

      return global.window.fetch('/foo', { method: 'GET' })
        .then(body => {
          expect(body.ok).toBeTruthy()
        })
        .catch(error => {
          expect(error).toBeFalsy()
        })
    })

    it('should not include the testURL in the call if not needed', () => {
      nock('http://sample.com').get('/foo').reply(200, { ok: true })

      return global.window.fetch('http://sample.com/foo', { method: 'GET' })
        .then(body => {
          expect(body.ok).toBeTruthy()
        })
        .catch(error => {
          expect(error).toBeFalsy()
        })
    })
  })
})
