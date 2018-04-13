/* global describe, it, expect */

import avro from 'avro-js'
import mockAvroSchema from '../mock/schema_input.mock'
import { Common } from '../components'

describe('common', () => {
  describe('schemaToMarkup', () => {
    it('should take a valid avro schema and generate nested markup', () => {
      const schema = Common.schemaToMarkup(mockAvroSchema)
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
