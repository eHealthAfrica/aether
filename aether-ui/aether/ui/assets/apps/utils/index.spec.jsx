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

/* global describe, it, expect */

import {
  clone,
  deepEqual,
  generateGUID,
  getLoggedInUser,
  isEmpty
} from './index'

describe('utils', () => {
  describe('clone', () => {
    it('should clone an obj', () => {
      const a = { foo: 11, bar: { baz: 22 } }
      const b = clone(a)
      expect(a).not.toBe(b)
      expect(b.foo).toBe(a.foo)
      expect(b.bar).not.toBe(a.bar)
    })
  })

  describe('generateGUID', () => {
    it('should match the simplest GUID regex', () => {
      const uuid = generateGUID()
      expect(uuid).toMatch(/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/)
    })
  })

  describe('deepEqual', () => {
    it('should compare different types', () => {
      expect(deepEqual(undefined, {})).toBeFalsy()
      expect(deepEqual(null, [])).toBeFalsy()
      expect(deepEqual('', {})).toBeFalsy()
      expect(deepEqual(NaN, [])).toBeFalsy()

      expect(deepEqual(1, {})).toBeFalsy()
      expect(deepEqual('1', [])).toBeFalsy()
      expect(deepEqual({}, [])).toBeFalsy()
      expect(deepEqual({ 0: 1 }, [1])).toBeFalsy()
    })

    it('should compare primitives', () => {
      expect(deepEqual(1, 1)).toBeTruthy()
      expect(deepEqual(1, 2)).toBeFalsy()
    })

    it('should compare objects', () => {
      const a = { foo: 11, bar: 22, baz: { y: 4 } }
      const b = { bar: 22, foo: 11, baz: { y: 4 } }
      expect(deepEqual(a, b)).toBeTruthy()
      b.baz.y = 5
      expect(deepEqual(a, b)).toBeFalsy()
      b.baz.y = 4
      b.baz.x = 1
      a.baz.z = 1
      expect(deepEqual(a, b)).toBeFalsy()
    })

    it('should compare arrays', () => {
      expect(deepEqual([1, 2, 3], [1, 2, 3])).toBeTruthy()
      expect(deepEqual([1, 2, 3], [1, 2])).toBeFalsy()
      expect(deepEqual([1, 2, 3], [1, 2, 2])).toBeFalsy()
    })

    it('should ignore null and undefined values', () => {
      const a = { x: 1, y: null, z: undefined }
      const b = { x: 1, z: null }
      expect(deepEqual(a, b, true)).toBeTruthy()
      expect(deepEqual(a, b)).toBeFalsy()
    })
  })

  describe('getLoggedInUserId', () => {
    it('should take logged in user from document', () => {
      expect(getLoggedInUser()).toEqual({ id: NaN, name: '' })

      const element = document.createElement('div')
      element.id = 'logged-in-user-info'
      element.setAttribute('data-user-id', '1')
      element.setAttribute('data-user-name', 'user')
      document.body.appendChild(element)

      expect(getLoggedInUser()).toEqual({ id: 1, name: 'user' })
    })
  })

  describe('isEmpty', () => {
    it('should detect null, undefined empty arrays, objects, strings but not "false" booleans', () => {
      expect(isEmpty(null)).toBeTruthy()
      expect(isEmpty(undefined)).toBeTruthy()
      expect(isEmpty('        ')).toBeTruthy()
      expect(isEmpty({})).toBeTruthy()
      expect(isEmpty([])).toBeTruthy()
      expect(isEmpty(false)).toBeFalsy()
    })
  })
})
