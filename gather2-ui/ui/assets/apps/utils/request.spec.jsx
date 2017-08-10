/* global describe, it */

import assert from 'assert'
import nock from 'nock'
import request from './request'

describe('request utils', () => {
  describe('request', () => {
    it('should do a GET request', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, {ok: true})

      return request('get', 'http://localhost/foo')
        .then((body) => {
          assert(body.ok, 'GET request should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
        })
    })

    it('should do a POST request', () => {
      nock('http://localhost')
        .post('/foo', {foo: 'bar'})
        .reply(200, {ok: true})

      return request('post', 'http://localhost/foo', {foo: 'bar'})
        .then((body) => {
          assert(body.ok, 'POST request should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
        })
    })

    it('should do a PUT request', () => {
      nock('http://localhost')
        .put('/foo', {foo: 'bar'})
        .reply(200, {ok: true})

      return request('put', 'http://localhost/foo', {foo: 'bar'})
        .then((body) => {
          assert(body.ok, 'PUT request should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
        })
    })

    it('should do a DELETE request', () => {
      nock('http://localhost')
        .delete('/foo')
        .reply(200, {ok: true})

      return request('delete', 'http://localhost/foo')
        .then((body) => {
          assert(body.ok, 'DELETE request should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
        })
    })
  })
})
