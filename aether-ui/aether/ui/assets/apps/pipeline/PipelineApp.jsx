import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Route } from 'react-router-dom'

import PipelineList from './PipelineList'
import Pipeline from './Pipeline'

class PipelineApp extends Component {
  render () {
    return (
      <Route render={props => (
        <React.Fragment>
          <Route exact path='/' component={PipelineList} />
          <Route path='/:id' component={Pipeline} />
        </React.Fragment>
      )} />
    )
  }
}

export default connect()(PipelineApp)
