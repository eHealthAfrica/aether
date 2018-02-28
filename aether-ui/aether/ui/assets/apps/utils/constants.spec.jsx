import { test, expect } from 'jest'
import * as constants from './constants.jsx'

test('constants', () => {
  expect(constants.KERNEL_APP).toBe('kernel')
  expect(constants.ODK_APP).toBe('odk')
  expect(constants.UI_APP).toBe('ui')
})
