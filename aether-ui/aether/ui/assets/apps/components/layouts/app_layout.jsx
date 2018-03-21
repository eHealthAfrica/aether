import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Route } from 'react-router-dom'
import { Home, Pipelines, NewPipeLine } from '../../components'

class AppLayout extends Component {
  render () {
    return (
      <Route render={props => (
        <div>
          <Route exact path='/' component={Home} />
          <Route path='/pipelines' component={Pipelines} />
          <Route path='/new-pipeline' component={NewPipeLine} />
        </div>
      )} />
    )
  }
}

const mapStateToProps = () => ({ })

export default connect(mapStateToProps, {})(AppLayout)
