const tap = require('tap')
const validation = require('../src/validation.js')
const validate = validation.validate

const locationSchema = {
  type: 'record',
  fields: [
    {
      name: 'latitude',
      type: 'float'
    },
    {
      name: 'longitude',
      type: 'float'
    }
  ]
}

const personSchema = {
  type: 'record',
  fields: [
    {
      name: 'firstName',
      type: 'string'
    },
    {
      name: 'lastName',
      type: 'string'
    },
    {
      name: 'age',
      type: 'int'
    }
  ]
}

const householdSchema = {
  type: 'record',
  fields: [
    {
      name: 'location',
      type: locationSchema
    },
    {
      name: 'persons',
      type: {
        type: 'array',
        items: personSchema
      }
    }
  ]
}

const entitySchema = {
  type: 'record',
  fields: [
    {
      name: 'coordinates',
      type: locationSchema
    },
    {
      name: 'ages',
      type: {
        type: 'array',
        items: 'int'
      }
    }
  ]
}

tap.test((t) => {
  const mappings = [
    [
      '$.location',
      '$.coordinates'
    ]
  ]
  const errors = validate({
    source: householdSchema,
    target: entitySchema,
    mappings: mappings
  })
  tap.ok(errors.length === 0)
  t.end()
})

tap.test((t) => {
  const mappings = [
    [
      '$.nonexistent',
      '$.coordinates'
    ]
  ]
  const errors = validate({
    source: householdSchema,
    target: entitySchema,
    mappings: mappings
  })
  tap.ok(errors.length === 1)
  tap.equal(errors[0].type, validation.JSONPATH_ERROR)
  tap.strictSame(errors[0].path, mappings[0][0])
  t.end()
})

tap.test((t) => {
  const mappings = [
    [
      '$.persons[*].age',
      '$.nonexistent'
    ]
  ]
  const errors = validate({
    source: householdSchema,
    target: entitySchema,
    mappings: mappings
  })
  tap.ok(errors.length === 1)
  tap.equal(errors[0].type, validation.JSONPATH_ERROR)
  tap.strictSame(errors[0].path, mappings[0][1])
  t.end()
})

tap.test((t) => {
  const mappings = [
    [
      '$.location',
      '$.coordinates'
    ]
  ]
  const invalidSchema = {name: 'a-string', type: 'string'}
  const errors = validate({
    source: invalidSchema,
    target: entitySchema,
    mappings: mappings
  })
  tap.ok(errors.length === 1)
  tap.equal(errors[0].type, validation.SCHEMA_ERROR)
  t.end()
})

tap.test((t) => {
  const mappings = [
    [
      '$.location',
      '$.coordinates'
    ]
  ]
  const invalidSchema = {not: 'avro'}
  const errors = validate({
    source: invalidSchema,
    target: invalidSchema,
    mappings: mappings
  })
  tap.ok(errors.length === 2)
  tap.equal(errors[0].type, validation.SCHEMA_ERROR)
  tap.equal(errors[1].type, validation.SCHEMA_ERROR)
  t.end()
})
