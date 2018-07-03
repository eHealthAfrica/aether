import React from 'react'
import ReactDOM from 'react-dom'

// https://reactjs.org/docs/portals.html

export default class Portal extends React.Component {
  constructor (props) {
    super(props)
    this.element = document.createElement('div')
  }

  componentDidMount () {
    // The portal element is inserted in the DOM tree after
    // the Modal's children are mounted, meaning that children
    // will be mounted on a detached DOM node. If a child
    // component requires to be attached to the DOM tree
    // immediately when mounted, for example to measure a
    // DOM node, or uses 'autoFocus' in a descendant, add
    // state to Modal and only render the children when Modal
    // is inserted in the DOM tree.
    document.body.appendChild(this.element)
  }

  componentWillUnmount () {
    document.body.removeChild(this.element)
  }

  render () {
    return ReactDOM.createPortal(
      this.props.children,
      this.element
    )
  }
}
