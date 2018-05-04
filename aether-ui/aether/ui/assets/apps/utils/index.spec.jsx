/* global describe, it, expect */

import {
  clone,
  generateGUID,
  deepEqual,
  getLoggedInUser,
  applyStyle,
  removeStyle
} from './index'

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

  describe('deepEqual', () => {
    it('should compare primitives', () => {
      let a = 1
      let b = 1
      expect(deepEqual(a, b)).toBeTruthy()
      b = 2
      expect(deepEqual(a, b)).toBeFalsy()
    })

    it('should compare objects', () => {
      let a = {foo: 11, bar: 22, baz: {y: 4}}
      let b = {bar: 22, foo: 11, baz: {y: 4}}
      expect(deepEqual(a, b)).toBeTruthy()
      b.baz.y = 5
      expect(deepEqual(a, b)).toBeFalsy()
      b.baz.y = 4
      b.baz.x = 1
      a.baz.z = 1
      expect(deepEqual(a, b)).toBeFalsy()
    })

    it('should compare arrays', () => {
      let a = [1, 2, 3]
      let b = [1, 2, 3]
      expect(deepEqual(a, b)).toBeTruthy()
      b = [1, 2]
      expect(deepEqual(a, b)).toBeFalsy()
      b = [1, 2, 2]
      expect(deepEqual(a, b)).toBeFalsy()
    })

    it('should ignore null and undefined values', () => {
      let a = {x: 1, y: null, z: undefined}
      let b = {x: 1, z: null}
      expect(deepEqual(a, b, true)).toBeTruthy()
      expect(deepEqual(a, b)).toBeFalsy()
    })
  })

  describe('getLoggedInUserId', () => {
    it('should take logged in user from document', () => {
      const element = document.createElement('div')
      element.id = 'logged-in-user-info'
      element.setAttribute('data-user-id', '1')
      element.setAttribute('data-user-name', 'user')
      document.body.appendChild(element)
      expect(getLoggedInUser()).toEqual({id: 1, name: 'user'})
    })
  })

  describe('applyStyle', () => {
    it('should apply the specified style to an element', () => {
      let element = document.createElement('div')
      element.id = 'test-element'
      document.body.appendChild(element)
      applyStyle('test-element', 'test-style')
      element = document.getElementById('test-element')
      expect(element.outerHTML).toEqual('<div id="test-element" class="test-style"></div>')
    })
  })

  describe('removeStyle', () => {
    it('should remove the specified style from an element', () => {
      let element = document.createElement('div')
      element.id = 'test-element'
      element.classList.add('test-style')
      document.body.appendChild(element)
      element = document.getElementById('test-element')
      expect(element.outerHTML).toEqual('<div id="test-element" class="test-style"></div>')
      removeStyle('test-element', 'test-style')
      element = document.getElementById('test-element')
      expect(element.outerHTML).toEqual('<div id="test-element" class=""></div>')
    })
  })
})
