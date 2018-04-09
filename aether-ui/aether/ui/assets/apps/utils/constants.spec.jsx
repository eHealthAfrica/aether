/* global test, expect */
import * as constants from './constants.jsx'

test('constants', () => {
  expect(constants.KERNEL_APP).toBe('kernel')
  expect(constants.UI_APP).toBe('ui')
  expect(constants.PROJECT_NAME).toBeDefined()
})
