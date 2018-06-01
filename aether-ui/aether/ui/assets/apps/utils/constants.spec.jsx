/* global test, expect */
import * as constants from './constants.jsx'

test('constants', () => {
  expect(constants.MAX_PAGE_SIZE).toBe(1048575)
  expect(constants.PROJECT_NAME).toBeDefined()
})
