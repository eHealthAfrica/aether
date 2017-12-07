/* global describe, it */

import assert from 'assert'
import { getType, flatten, inflate } from './types'

describe('types', () => {
  describe('getType', () => {
    it('should return null with useless values', () => {
      assert.equal(getType(), null)
      assert.equal(getType(null), null)
      assert.equal(getType(''), null)
      assert.equal(getType('   '), null)
      assert.equal(getType([]), null)
      assert.equal(getType({}), null)
      assert.equal(getType(() => {}), null)
    })

    it('should indicate if the value is an object', () => {
      assert.equal(getType({a: 1}), 'object')
    })

    it('should indicate if the value is an array', () => {
      assert.equal(getType([1, 2, 3]), 'array')
    })

    it('should indicate if the value is a boolean', () => {
      assert.equal(getType(true), 'bool')
      assert.equal(getType(false), 'bool')
    })

    it('should indicate if the value is a number', () => {
      assert.equal(getType(0), 'int')
      assert.equal(getType(1.0), 'int')
      assert.equal(getType(1.9), 'float')
    })

    it('should indicate if the value is a date', () => {
      assert.equal(getType(new Date()), 'datetime')
      assert.equal(getType('1999-01-01T23:59:59.9+01:00'), 'datetime')
      assert.equal(getType('1999-01-01T23:59:59.999Z'), 'datetime')
      assert.equal(getType('1999-01-01'), 'date')
      assert.equal(getType('23:59:59'), 'time')
    })

    it('default type is string', () => {
      assert.equal(getType('true'), 'string')
      assert.equal(getType('false'), 'string')

      assert.equal(getType('0'), 'string')
      assert.equal(getType('1.0'), 'string')
      assert.equal(getType('1.9'), 'string')

      assert.equal(getType('1999-01-01T23:59:59'), 'string')
      assert.equal(getType('1999-13-01'), 'string')
      assert.equal(getType('24:59:59'), 'string')
      assert.equal(getType('23:60:59'), 'string')
      assert.equal(getType('23:59:60'), 'string')

      assert.equal(getType('abc'), 'string')
    })
  })

  describe('flatten', () => {
    it('should flatten JSON objects', () => {
      const entry = {
        a: {
          b: {
            c: {
              d: 1
            }
          }
        }
      }

      assert.deepEqual(flatten(entry), { 'a.b.c.d': 1 })
    })

    it('should not flatten array properties', () => {
      const entry = {
        a: {
          b: {
            c: {
              d: 1
            },
            a: [1, 2, {}, {d: 1}]
          }
        }
      }

      assert.deepEqual(flatten(entry), { 'a.b.c.d': 1, 'a.b.a': [1, 2, {}, {d: 1}] })
    })
  })

  describe('inflate', () => {
    it('should return empty array', () => {
      assert.deepEqual(inflate([]), [])
    })

    it('should analyze flat JSON objects', () => {
      const keys = [
        'a|b|c',
        'a|b|d',
        'a|e|f',
        'a|g',
        'h'
      ]

      const expectedValue = [
        {
          'a': { key: 'a', path: 'a', label: 'a', siblings: 4, hasChildren: true, isLeaf: false },
          'h': { key: 'h', path: 'h', label: 'h', siblings: 1, hasChildren: false, isLeaf: true }
        },
        {
          'a|b': { key: 'a|b', path: 'a.b', label: 'b', siblings: 2, hasChildren: true, isLeaf: false },
          'a|e': { key: 'a|e', path: 'a.e', label: 'e', siblings: 1, hasChildren: true, isLeaf: false },
          'a|g': { key: 'a|g', path: 'a.g', label: 'g', siblings: 1, hasChildren: false, isLeaf: true }
        },
        {
          'a|b|c': { key: 'a|b|c', path: 'a.b.c', label: 'c', siblings: 1, hasChildren: false, isLeaf: true },
          'a|b|d': { key: 'a|b|d', path: 'a.b.d', label: 'd', siblings: 1, hasChildren: false, isLeaf: true },
          'a|e|f': { key: 'a|e|f', path: 'a.e.f', label: 'f', siblings: 1, hasChildren: false, isLeaf: true }
        }
      ]

      assert.deepEqual(inflate(keys, '|'), expectedValue)
    })
  })
})
