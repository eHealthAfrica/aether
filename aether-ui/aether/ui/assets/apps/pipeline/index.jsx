import React from 'react'
import { render } from 'react-dom'
import { hot } from 'react-hot-loader'

import { AppLayout } from '../components'
import PipelineApp from './PipelineApp'

const appElement = document.getElementById('pipeline-app')
const component = <AppLayout app={PipelineApp} />
console.log(component)
render(component, appElement)

// Include this to enable HMR for this module
hot(module)(component)
