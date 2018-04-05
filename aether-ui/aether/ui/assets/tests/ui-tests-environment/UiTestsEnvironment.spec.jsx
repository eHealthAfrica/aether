import nock from 'nock'

describe('test environment', () => {
  it('should set jsdom, range and window.fetch on its global object', () => {
    expect(global.jsdom).toBeTruthy()
    expect(global.range).toBeTruthy()
    expect(global.window.fetch).toBeTruthy()
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
      nock('http://localhost').get('/foo').reply(200, {ok: true})

      return global.window.fetch('/foo', {method: 'GET'})
        .then(body => {
          expect(body.ok).toBeTruthy()
        })
        .catch(error => {
          expect(error).toBeFalsy()
        })
    })

    it('should not include the testURL in the call if not needed', () => {
      nock('http://sample.com').get('/foo').reply(200, {ok: true})

      return global.window.fetch('http://sample.com/foo', {method: 'GET'})
        .then(body => {
          expect(body.ok).toBeTruthy()
        })
        .catch(error => {
          expect(error).toBeFalsy()
        })
    })
  })
})
