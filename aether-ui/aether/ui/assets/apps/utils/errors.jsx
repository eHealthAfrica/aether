class HTTPError extends Error {
  constructor (message, error, status) {
    super(message)
    this.error = error
    this.status = status
  }
}

class NotFoundError extends HTTPError {
  constructor (message, error = 'Not Found', status = 404) {
    super(message, error, status)
  }
}

export { NotFoundError, HTTPError }
