/* global describe, it */

import assert from 'assert'
import nock from 'nock'

import {
  deleteData,
  fetchUrls,
  forceGetData,
  getData,
  patchData,
  postData,
  putData
} from './request'

describe('request utils', () => {
  describe('request', () => {
    it('should do a GET request', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(200, {ok: true})

      return getData('http://localhost/foo')
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

      return postData('http://localhost/foo', {foo: 'bar'})
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

      return putData('http://localhost/foo', {foo: 'bar'})
        .then((body) => {
          assert(body.ok, 'PUT request should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
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
        .then((body) => {
          assert(body.ok, 'Fake PUT request should return true')
          assert(body.put)
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
        })
    })

    it('should do a PATCH request', () => {
      nock('http://localhost')
        .patch('/foo', {foo: 'bar'})
        .reply(200, {ok: true})

      return patchData('http://localhost/foo', {foo: 'bar'})
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

      return deleteData('http://localhost/foo')
        .then((body) => {
          assert(body.ok, 'DELETE request should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
        })
    })

    it('should throw an error', () => {
      nock('http://localhost')
        .get('/foo')
        .reply(404, {ok: false, message: 'something went wrong'})

      return getData('http://localhost/foo')
        .then((body) => {
          assert(!body, 'Unexpected response')
        })
        .catch((error) => {
          assert(error, 'Expected error')
          assert.equal(error.message, 'Not Found', '404 error message')
          error.response.then(response => {
            assert(!response.ok)
            assert.equal(response.message, 'something went wrong')
          })
        })
    })
  })

  describe('forceGetData', () => {
    it('should return a GET request', () => {
      nock('http://localhost')
        .get('/get')
        .reply(200, {ok: true})

      return forceGetData('http://localhost/get', 'http://localhost/post', {foo: 'bar'})
        .then((body) => {
          assert(body.ok, 'Should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
        })
    })

    it('should FORCE a GET request', () => {
      nock('http://localhost')
        .get('/get')
        .reply(404, {ok: false, message: 'something went wrong'})

      nock('http://localhost')
        .post('/post', {foo: 'bar'})
        .reply(200, {ok: true})

      nock('http://localhost')
        .get('/get')
        .reply(200, {ok: true})

      return forceGetData('http://localhost/get', 'http://localhost/post', {foo: 'bar'})
        .then((body) => {
          assert(body.ok, 'Should return true')
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
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
        .then((payload) => {
          assert.deepEqual(payload.first, {ok: true, content: 'something'})
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
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
        .then((payload) => {
          assert.deepEqual(payload,
            {
              first: {ok: true, content: 'something'},
              second: {ok: true, content: 'else'}
            }
          )
        })
        .catch((error) => {
          assert(!error, 'Unexpected error')
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
        .then((body) => {
          assert(!body, 'Unexpected response')
        })
        .catch((error) => {
          assert(error, 'Expected error', error)
          // it throws the first error and does not continue with the rest of Promises
          assert.equal(error.message, 'Bad Request', '400 error message')
          error.response.then(response => {
            assert(!response.ok)
            assert.equal(response.message, 'something went wrong')
          })
        })
    })
  })
})
