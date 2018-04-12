import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Route } from 'react-router-dom'

import PipelineList from './PipelineList'
import Pipeline from './Pipeline'
import NewPipeline from './NewPipeline'

class PipelineApp extends Component {
  render () {
    return (
      <Route render={props => (
        <React.Fragment>
          <Route exact path='/' component={PipelineList} />
          <Route path='/pipeline' component={Pipeline} />
          <Route path='/new-pipeline' component={NewPipeline} />
        </React.Fragment>
      )} />
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(PipelineApp)
