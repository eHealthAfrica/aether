/* This function is used as a typeHook option by `avro.Type.forValue().
 * Background: when deriving avro schemas from sample data, all records, enums, and
 * fixed avro types will be anonymous. Using the `typeHook` option, we can pass in
 * a name generator which allows to maintain compatibility with other avro
 * libraries such as python-spavro.
 *
 *    See: https://github.com/mtth/avsc/issues/108#issuecomment-302436388
 */
export const generateSchemaName = (prefix) => {
  let index = 0
  return (schema) => {
    switch (schema.type) {
      case 'enum':
      case 'fixed':
      case 'record':
        schema.name = `${prefix}_${index++}`
        break
      default:
    }
  }
}
