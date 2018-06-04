/* global describe, it, expect */

import client from './client'

describe('Request middleware', () => {
  it('should be a function', () => {
    expect(typeof client).toEqual('function')
  })
})
