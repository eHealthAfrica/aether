/* global describe, it, expect, beforeEach, afterEach */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'
import nock from 'nock'

import EmptyAlert from './EmptyAlert'
import FetchErrorAlert from './FetchErrorAlert'
import PaginationBar from './PaginationBar'
import PaginationContainer from './PaginationContainer'
import RefreshSpinner from './RefreshSpinner'
import LoadingSpinner from './LoadingSpinner'

class Foo extends React.Component {
  render () {
    return 'foo'
  }
}

describe('PaginationContainer', () => {
  describe('workflow', () => {
    let component = null

    beforeEach(() => {
      nock('http://localhost')
        .get('/foo')
        .query(true)
        .reply()

      component = mountWithIntl(
        <PaginationContainer
          listComponent={Foo}
          url='http://localhost/foo'
        />
      )

      expect(component.state('isLoading')).toBeTruthy()
    })

    afterEach(() => {
      nock.isDone()
      nock.cleanAll()
      component.unmount()
      component = null
    })

    it('should render the loading spinner', () => {
      component.setState({
        isLoading: true,
        isRefreshing: false,
        error: false,
        list: null
      })

      expect(component.find(LoadingSpinner).exists()).toBeTruthy()
      expect(component.find(FetchErrorAlert).exists()).toBeFalsy()
      expect(component.find('[data-qa="data-loaded"]').exists()).toBeFalsy()
      expect(component.find(PaginationBar).exists()).toBeFalsy()
      expect(component.find(EmptyAlert).exists()).toBeFalsy()
      expect(component.find(RefreshSpinner).exists()).toBeFalsy()
      expect(component.find(Foo).exists()).toBeFalsy()
    })

    it('should render the fetch error warning', () => {
      component.setState({
        isLoading: false,
        isRefreshing: false,
        error: true,
        list: null
      })

      expect(component.find(LoadingSpinner).exists()).toBeFalsy()
      expect(component.find(FetchErrorAlert).exists()).toBeTruthy()
      expect(component.find('[data-qa="data-loaded"]').exists()).toBeFalsy()
      expect(component.find(PaginationBar).exists()).toBeFalsy()
      expect(component.find(EmptyAlert).exists()).toBeFalsy()
      expect(component.find(RefreshSpinner).exists()).toBeFalsy()
      expect(component.find(Foo).exists()).toBeFalsy()
    })

    it('should render the empty warning and the list component', () => {
      component.setState({
        isLoading: false,
        isRefreshing: false,
        error: false,
        list: {
          count: 0,
          results: []
        }
      })

      expect(component.find(LoadingSpinner).exists()).toBeFalsy()
      expect(component.find(FetchErrorAlert).exists()).toBeFalsy()
      expect(component.find('[data-qa="data-loaded"]').exists()).toBeTruthy()
      expect(component.find(PaginationBar).exists()).toBeTruthy()
      expect(component.find(EmptyAlert).exists()).toBeTruthy()
      expect(component.find(RefreshSpinner).exists()).toBeFalsy()
      expect(component.find(Foo).exists()).toBeTruthy()
    })

    it('should render the refresh spinner and the list component', () => {
      component.setState({
        isLoading: false,
        isRefreshing: true,
        error: false,
        list: {
          count: 1,
          results: [1]
        }
      })

      expect(component.find(LoadingSpinner).exists()).toBeFalsy()
      expect(component.find(RefreshSpinner).exists()).toBeTruthy()
      expect(component.find(FetchErrorAlert).exists()).toBeFalsy()
      expect(component.find('[data-qa="data-loaded"]').exists()).toBeTruthy()
      expect(component.find(PaginationBar).exists()).toBeTruthy()
      expect(component.find(EmptyAlert).exists()).toBeFalsy()
      expect(component.find(Foo).exists()).toBeTruthy()
      expect(component.text()).toEqual('foo')
    })

    it('should render the list component', () => {
      component.setState({
        isLoading: false,
        isRefreshing: false,
        error: false,
        list: {
          count: 1,
          results: [1]
        }
      })

      expect(component.find(RefreshSpinner).exists()).toBeFalsy()
      expect(component.find(FetchErrorAlert).exists()).toBeFalsy()
      expect(component.find('[data-qa="data-loaded"]').exists()).toBeTruthy()
      expect(component.find(PaginationBar).exists()).toBeTruthy()
      expect(component.find(EmptyAlert).exists()).toBeFalsy()
      expect(component.find(Foo).exists()).toBeTruthy()
      expect(component.text()).toEqual('foo')
    })

    it('should change current page to 1 if pageSize is changed', () => {
      component.setState({ page: 14, pageSize: 100 })
      expect(component.state('page')).toEqual(14)
      expect(component.state('pageSize')).toEqual(100)

      component.setProps({ pageSize: 100 })
      expect(component.state('page')).toEqual(14)
      expect(component.state('pageSize')).toEqual(100)

      component.setProps({ pageSize: 10 })
      expect(component.state('page')).toEqual(1)
      expect(component.state('pageSize')).toEqual(10)
    })
  })

  describe('PaginationBar iterations', () => {
    let component = null
    let paginationBar = null

    beforeEach(async () => {
      nock('http://localhost')
        .get('/foo')
        .query(true)
        .reply(200)
        .persist()

      component = mountWithIntl(
        <PaginationContainer
          listComponent={Foo}
          url='http://localhost/foo'

          search
          showFirst
          showPrevious
          showNext
          showLast
        />
      )

      expect(component.state('page')).toEqual(1)
      expect(component.state('search')).toBeFalsy()

      component.setState({
        isLoading: false,
        isRefreshing: false,
        error: false,
        list: {
          count: 100,
          results: global.range(0, 100)
        },
        search: 'bla, bla',
        page: 2
      })

      component.update()
      expect(component.state('page')).toEqual(2)
      expect(component.state('search')).toEqual('bla, bla')

      paginationBar = component.find(PaginationBar)
      expect(paginationBar.exists()).toBeTruthy()
    })

    afterEach(() => {
      nock.isDone()
      nock.cleanAll()
      component.unmount()
      component = null
      paginationBar = null
    })

    it('Search actions should change the current page to 1', () => {
      expect(component.state('page')).toEqual(2)
      expect(component.state('search')).toEqual('bla, bla')

      const input = paginationBar.find('[data-qa="data-pagination-search"]').find('input')
      expect(input.exists()).toBeTruthy()

      input.simulate('change', {target: {name: 'search', value: 'something'}})
      input.simulate('keypress', {charCode: 13})

      expect(component.state('page')).toEqual(1)
      expect(component.state('search')).toEqual('something')
    })

    it('Navigation buttons should change the current page, but not search', () => {
      expect(component.state('page')).toEqual(2)
      expect(component.state('search')).toEqual('bla, bla')

      const nextButton = paginationBar.find('[data-qa="data-pagination-next"]').find('button')
      expect(nextButton.exists()).toBeTruthy()

      nextButton.simulate('click')

      expect(component.state('page')).toEqual(3)
      expect(component.state('search')).toEqual('bla, bla')
    })
  })
})
