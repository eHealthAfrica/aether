/* global describe, it, expect */

import avro from 'avro-js'
import { clone, generateGUID, getLoggedInUser, schemaToMarkup } from './index'
import mockAvroSchema from '../mock/schema_input.mock'

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

  describe('schemaToMarkup', () => {
    it('should take a valid avro schema and generate nested markup', () => {
      const schema = schemaToMarkup(mockAvroSchema)
      expect(schema[0].props.children.length).toEqual(2)
      expect(schema[0].props.children[1].props.children.props.children.length).toEqual(7)
      expect(schema[0].props.children[1].props.children.props.children[0][0][0].key).toEqual('person')
    })

    it('should take a invalid avro schema and throw and error', () => {
      delete mockAvroSchema['name']
      let schema = null
      try {
        schema = avro.parse(mockAvroSchema)
      } catch (error) {
        expect(error.toString()).toEqual(expect.stringContaining('missing name property in schema'))
      }

      expect(schema).toBe(null)
    })
  })
})
