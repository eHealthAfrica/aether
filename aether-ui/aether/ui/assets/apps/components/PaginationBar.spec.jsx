/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import PaginationBar from './PaginationBar'

describe('PaginationBar', () => {
  it('should NOT render with less than 2 pages and without active "search"', () => {
    const component = mountWithIntl(
      <PaginationBar
        currentPage={1}
        pageSize={10}
        records={5}
        goToPage={() => {}}
      />
    )

    expect(component.find('[data-qa="data-pagination"]').exists()).toBeFalsy()
    expect(component.text()).toEqual('')
  })

  it('should render with less than 2 pages but with "search"', () => {
    const component = mountWithIntl(
      <PaginationBar
        currentPage={1}
        pageSize={10}
        records={0}
        goToPage={() => {}}
        search
      />
    )

    component.setState({search: 'something'})
    expect(component.state('search')).toEqual('something')

    expect(component.find('[data-qa="data-pagination"]').exists()).toBeTruthy()
    expect(component.find('[data-qa="data-pagination-search"]').exists()).toBeTruthy()
    expect(component.find('[data-qa="data-pagination-buttons"]').exists()).toBeFalsy()
  })

  describe('Search bar', () => {
    it('should NOT render the search bar without "search"', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={3}
          pageSize={10}
          records={50}
          goToPage={() => {}}
        />
      )

      expect(component.find('[data-qa="data-pagination"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-search"]').exists()).toBeFalsy()
    })

    it('should render the search bar with "search"', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={3}
          pageSize={10}
          records={50}
          goToPage={() => {}}
          search
        />
      )

      expect(component.find('[data-qa="data-pagination"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-search"]').exists()).toBeTruthy()
    })

    it('should trigger "onSearch" after pressing "Enter"', () => {
      let text = null
      const component = mountWithIntl(
        <PaginationBar
          currentPage={3}
          pageSize={10}
          records={50}
          goToPage={() => {}}
          onSearch={(value) => { text = value }}
          search
        />
      )

      expect(text).toBeNull()
      const input = component.find('[data-qa="data-pagination-search"]').find('input')

      // "change" event does not trigger `onSearch`
      input.simulate('change', {target: {name: 'search', value: 'something'}})
      expect(text).toBeNull()

      // "onKeyPress" Any key does not trigger `onSearch`
      input.simulate('keypress', {charCode: 90})
      expect(text).toBeNull()

      // "onKeyPress" Enter does trigger `onSearch`
      input.simulate('keypress', {charCode: 13})
      expect(text).toEqual('something')
    })
  })

  describe('Navigation buttons', () => {
    it('should render the navigation buttons with more than 1 page', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={1}
          pageSize={10}
          records={12}
          goToPage={() => {}}
        />
      )

      expect(component.find('[data-qa="data-pagination"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-search"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-buttons"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-page"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-total"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-total"]').text()).toEqual('2')
    })

    it('should render "Record" with page size 1', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={1}
          pageSize={1}
          records={12}
          goToPage={() => {}}
        />
      )

      expect(component.find('[data-qa="data-pagination-buttons"]').text()).toContain('Record')
    })

    it('should render "Page" with page size greater than 1', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={1}
          pageSize={2}
          records={12}
          goToPage={() => {}}
        />
      )

      expect(component.find('[data-qa="data-pagination-buttons"]').text()).toContain('Page')
    })

    it('should NOT render the ANY navigation button without "showXXX" only currentPage', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={4}
          pageSize={10}
          records={250}
          goToPage={() => {}}
        />
      )

      expect(component.find('[data-qa="data-pagination-page"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeFalsy()
    })

    it('should render the navigation button with "showXXX"', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={1}
          pageSize={10}
          records={50}
          goToPage={() => {}}
          showFirst
          showPrevious
          showNext
          showLast
        />
      )
      expect(component.find('[data-qa="data-pagination-total"]').text()).toEqual('5')

      // FIRST page
      expect(component.find('[name="currentPage"]').props().value).toEqual(1)
      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeTruthy()

      // SECOND page
      component.setProps({currentPage: 2})
      expect(component.find('[name="currentPage"]').props().value).toEqual(2)

      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeTruthy()

      // between SECOND and PREVIOUS LAST page
      component.setProps({currentPage: 3})
      expect(component.find('[name="currentPage"]').props().value).toEqual(3)
      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeTruthy()

      // PREVIOUS LAST
      component.setProps({currentPage: 4})
      expect(component.find('[name="currentPage"]').props().value).toEqual(4)
      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeTruthy()

      // LAST
      component.setProps({currentPage: 5})
      expect(component.find('[name="currentPage"]').props().value).toEqual(5)
      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeFalsy()
    })

    it('should render the PREVIOUS button if "currentPage" = 2 without "showFirst"', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={2}
          pageSize={10}
          records={15}
          goToPage={() => {}}
          showPrevious
        />
      )

      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeFalsy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeTruthy()
    })

    it('should render the NEXT button if "nextPage" = "lastPage" without "showLast"', () => {
      const component = mountWithIntl(
        <PaginationBar
          currentPage={1}
          pageSize={10}
          records={15}
          goToPage={() => {}}
          showNext
        />
      )

      expect(component.find('[data-qa="data-pagination-total"]').text()).toEqual('2')
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeFalsy()
    })

    it('should navigate with buttons', () => {
      const currentPage = 3
      let page = 0
      const component = mountWithIntl(
        <PaginationBar
          currentPage={currentPage}
          pageSize={10}
          records={50}
          goToPage={(newPage) => { page = newPage }}
          showFirst
          showPrevious
          showNext
          showLast
        />
      )
      // all buttons are visible
      expect(component.find('[data-qa="data-pagination-first"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-previous"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-next"]').exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-last"]').exists()).toBeTruthy()

      expect(component.find('[data-qa="data-pagination-total"]').text()).toEqual('5')
      expect(component.find('[name="currentPage"]').props().value).toEqual(currentPage)

      expect(page).toEqual(0)
      component.find('[data-qa="data-pagination-first"]').find('button').simulate('click')
      expect(page).toEqual(1)
      component.find('[data-qa="data-pagination-previous"]').find('button').simulate('click')
      expect(page).toEqual(currentPage - 1)
      component.find('[data-qa="data-pagination-next"]').find('button').simulate('click')
      expect(page).toEqual(currentPage + 1)
      component.find('[data-qa="data-pagination-last"]').find('button').simulate('click')
      expect(page).toEqual(5)
    })

    it('should navigate with current page input', () => {
      const currentPage = 3
      let page = 0
      const component = mountWithIntl(
        <PaginationBar
          currentPage={currentPage}
          pageSize={10}
          records={50}
          goToPage={(newPage) => { page = newPage }}
          showFirst
          showPrevious
          showNext
          showLast
        />
      )
      const input = component.find('[data-qa="data-pagination-page"]').find('input')
      expect(input.exists()).toBeTruthy()
      expect(component.find('[data-qa="data-pagination-total"]').text()).toEqual('5')
      expect(component.find('[name="currentPage"]').props().value).toEqual(currentPage)

      expect(page).toEqual(0)

      // "blur" event does not trigger `goToPage` with same "currentPage"
      input.simulate('blur')
      expect(page).toEqual(0)

      // "click" event does not trigger `goToPage`
      input.simulate('click')
      expect(page).toEqual(0)

      // "change" event does not trigger `goToPage`
      // negative numbers are replaced with first page
      input.simulate('change', {target: {value: '-2'}})
      expect(component.find('[name="currentPage"]').props().value).toEqual(1)
      expect(page).toEqual(0)

      // too big numbers are replaced with last page
      input.simulate('change', {target: {value: '20'}})
      expect(component.find('[name="currentPage"]').props().value).toEqual(5)
      expect(page).toEqual(0)

      // no values are replaced with first page
      input.simulate('change', {target: {}})
      expect(component.find('[name="currentPage"]').props().value).toEqual(1)
      expect(page).toEqual(0)

      input.simulate('change', {target: {value: '2'}})
      expect(component.find('[name="currentPage"]').props().value).toEqual(2)
      expect(page).toEqual(0)

      // "blur" event does trigger `goToPage`
      input.simulate('blur')
      expect(page).toEqual(2)
    })
  })
})
