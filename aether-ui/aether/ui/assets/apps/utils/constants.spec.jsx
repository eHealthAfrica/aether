/* global test, expect */
import * as constants from './constants.jsx'

test('constants', () => {
  expect(constants.MAX_PAGE_SIZE).toBe(5000)
  expect(constants.PROJECT_NAME).toBeDefined()
})
