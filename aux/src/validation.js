const avro = require('avsc')
const jsonpath = require('jsonpath')

const JSONPATH_ERROR = 'JSONPATH_ERROR'
const SCHEMA_ERROR = 'SCHEMA_ERROR'

const validatePath = (obj, path) => {
  let result
  try {
    result = jsonpath.query(obj, path)
  } catch (error) {
    return {
      error: {
        type: SCHEMA_ERROR,
        data: obj,
        description: 'Not a valid avro schema'
      },
      result: null
    }
  }
  if (result.length > 0) {
    return {
      error: null,
      result: result
    }
  } else {
    return {
      error: {
        type: JSONPATH_ERROR,
        path: path
      },
      result: null
    }
  }
}

const forSchema = (obj) => {
  try {
    return {
      error: null,
      result: avro.Type.forSchema(obj)
    }
  } catch (error) {
    return {
      error: {
        type: SCHEMA_ERROR,
        data: obj,
        description: 'Not a valid avro schema'
      },
      result: null
    }
  }
}

const validate = ({
  source,
  target,
  mappings
}) => {
  const sourceType = forSchema(source)
  const targetType = forSchema(target)

  const schemaErrors = [sourceType, targetType].filter((obj) => {
    return obj.error
  })
  if (schemaErrors.length) {
    return schemaErrors.map((obj) => obj.error)
  }

  return mappings.reduce((errors, mapping) => {
    const [getter, setter] = mapping
    const sourceResult = validatePath(sourceType.result.random(), getter)
    const targetResult = validatePath(targetType.result.random(), setter)
    if (sourceResult.error) {
      errors.push(sourceResult.error)
    }
    if (targetResult.error) {
      errors.push(targetResult.error)
    }
    return errors
  }, [])
}

exports.JSONPATH_ERROR = JSONPATH_ERROR
exports.SCHEMA_ERROR = SCHEMA_ERROR
exports.validatePath = validatePath
exports.validate = validate
