/* global describe, it, beforeEach, afterEach */

import assert from 'assert'
import nock from 'nock'
import {
  deleteData,
  fetchUrls,
  getData,
  patchData,
  postData,
  putData
} from './request'

describe('request utils', () => {
  beforeEach(() => {
    nock.cleanAll()
  })

  afterEach(() => {
    nock.isDone()
    nock.cleanAll()
  })

  describe('request', () => {
    it('should do a GET request', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, {ok: true})

      return getData('http://localhost/foo')
        .then(body => {
          assert(body.ok, 'GET request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a GET request and return TEXT', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, 'text', {'Content-Type': 'text/plain'})

      return getData('http://localhost/foo')
        .then(body => {
          assert.equal(body, 'text')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a GET request and download response', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, 'content text')

      let createObjectURLCalled = false
      let revokeObjectURLCalled = false

      window.URL = {
        createObjectURL: (content) => {
          assert(content)
          createObjectURLCalled = true
        },
        revokeObjectURL: (url) => {
          assert.equal(url, 'http://localhost/foo')
          revokeObjectURLCalled = true
        }
      }

      return getData('http://localhost/foo', {blob: true})
        .then(body => {
          assert(!body, `No expected response ${body}`)
          assert(createObjectURLCalled, 'createObjectURL was called')
          assert(revokeObjectURLCalled, 'revokeObjectURL was called')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a POST request', () => {
      nock('http://localhost')
        .post('/foo', {foo: 'bar'})
        .reply(200, {ok: true})

      return postData('http://localhost/foo', {foo: 'bar'})
        .then(body => {
          assert(body.ok, 'POST request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a PUT request', () => {
      nock('http://localhost')
        .put('/foo', {foo: 'bar'})
        .reply(200, {ok: true})

      return putData('http://localhost/foo', {foo: 'bar'})
        .then(body => {
          assert(body.ok, 'PUT request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a PUT request using FormData', () => {
      nock('http://localhost')
        .put('/foo')
        .reply(200, {ok: true})

      return putData(
        'http://localhost/foo',
        {foo: 'bar', list: [1, 2, 3], useless: null, nothing: undefined},
        {multipart: true}
      )
        .then(body => {
          assert(body.ok, 'PUT request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a fake PUT request', () => {
      nock('http://localhost')
        .put('/foo')
        .reply(200, {ok: true, put: true})

      nock('http://localhost')
        .post('/foo')
        .reply(400, {ok: false, put: false})

      return postData('http://localhost/foo', {foo: 'bar'}, {multipart: true})
        .then(body => {
          assert(body.ok, 'Fake PUT request should return true')
          assert(body.put)
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a PATCH request', () => {
      nock('http://localhost')
        .patch('/foo', {foo: 'bar'})
        .reply(200, {ok: true})

      return patchData('http://localhost/foo', {foo: 'bar'})
        .then(body => {
          assert(body.ok, 'PUT request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do a DELETE request', () => {
      nock('http://localhost')
        .delete('/foo')
        .reply(204)

      return deleteData('http://localhost/foo')
        .then(body => {
          assert.deepEqual(body, {}, 'DELETE request should return an empty object')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should correctly turn a params object into a query string 1', () => {
      nock('http://localhost')
        .get('/foo')
        .query({ kartoffel: '9', ingwer: 'False' })
        .reply(200, {ok: true})

      return getData('http://localhost/foo', {params: { kartoffel: 9, ingwer: 'False' }})
        .then(body => {
          assert(body.ok, 'GET request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should correctly turn a params object into a query string 2', () => {
      nock('http://localhost')
        .get('/foo')
        .query({ kartoffel: '9', ingwer: 'False' })
        .reply(200, {ok: true})

      return getData('http://localhost/foo?kartoffel=9', {params: { ingwer: 'False' }})
        .then(body => {
          assert(body.ok, 'GET request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should correctly turn a params object into a query string 3', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, {ok: true})

      return getData('http://localhost/foo', {params: { useless: '' }})
        .then(body => {
          assert(body.ok, 'GET request should return true')
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should throw an error', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(404)

      return getData('http://localhost/foo')
        .then(body => {
          assert(!body, `Unexpected response ${body}`)
        })
        .catch(error => {
          assert(error, 'Expected error')
          assert.equal(error.message, 'Not Found', '404 error message')
        })
    })
  })

  describe('fetchUrls', () => {
    it('should do a GET request', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, {ok: true, content: 'something'})

      return fetchUrls([{
        name: 'first',
        url: 'http://localhost/foo'
      }])
        .then(payload => {
          assert.deepEqual(payload.first, {ok: true, content: 'something'})
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should do more than one GET request', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, {ok: true, content: 'something'})
      nock('http://localhost')
        .get('/bar')
        .reply(200, {ok: true, content: 'else'})

      return fetchUrls([
        {
          name: 'first',
          url: 'http://localhost/foo'
        },
        {
          name: 'second',
          url: 'http://localhost/bar'
        }
      ])
        .then(payload => {
          assert.deepEqual(payload,
            {
              first: {ok: true, content: 'something'},
              second: {ok: true, content: 'else'}
            }
          )
        })
        .catch(error => {
          assert(!error, `Unexpected error ${error}`)
        })
    })

    it('should throw an error', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(400, {ok: false, message: 'something went wrong'})
      nock('http://localhost')
        .get('/bar')
        .reply(404, {ok: false, message: 'something went really wrong'})

      return fetchUrls([
        {
          name: 'first',
          url: 'http://localhost/foo'
        },
        {
          name: 'second',
          url: 'http://localhost/bar'
        }
      ])
        .then(body => {
          assert(!body, `Unexpected response ${body}`)
        })
        .catch(error => {
          assert(error, 'Expected error')
          // it throws the first error and does not continue with the rest of Promises
          assert.equal(error.message, 'Bad Request', '400 error message')
        })
    })
  })
})
