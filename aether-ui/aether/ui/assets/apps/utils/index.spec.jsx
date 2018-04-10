/* global describe, it, expect */

import { generateGUID } from './index'

describe('utils', () => {
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
