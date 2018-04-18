import ReactDOM from 'react-dom'

export const isMounted = (Component) => {
  try {
    ReactDOM.findDOMNode(Component)
    return true
  } catch (e) {
    return false
  }
}
