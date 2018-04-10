/* global describe, it, expect */

import { clone, generateGUID } from './index'

describe('utils', () => {
  describe('clone', () => {
    it('should clone an obj', () => {
      const a = {foo: 11, bar: {baz: 22}}
      const b = clone(a)
      expect(a).not.toBe(b)
      expect(b.foo).toBe(a.foo)
      expect(b.bar).not.toBe(a.bar)
    })
  })

  describe('generateGUID', () => {
    it('should match the simplest GUID regex', () => {
      const uuid = generateGUID()

      expect(uuid).toBeTruthy()
      expect(uuid.length).toEqual(36)
      expect(uuid.charAt(8)).toEqual('-')
      expect(uuid.charAt(13)).toEqual('-')
      expect(uuid.charAt(18)).toEqual('-')
      expect(uuid.charAt(23)).toEqual('-')
    })
  })
})
