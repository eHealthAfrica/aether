class HTTPError extends Error {
  constructor (message, error, status) {
    super(message)
    this.error = error
    this.status = status
  }
}

class BadRequestError extends HTTPError {
  constructor (message, error = 'Bad Request', status = 400) {
    super(message, error, status)
  }
}

class UnauthorizedError extends HTTPError {
  constructor (message, error = 'Unauthorized', status = 401) {
    super(message, error, status)
  }
}

class NotFoundError extends HTTPError {
  constructor (message, error = 'Not Found', status = 404) {
    super(message, error, status)
  }
}

class ConflictError extends HTTPError {
  constructor (message, error = 'Conflict', status = 409) {
    super(message, error, status)
  }
}

export { BadRequestError, UnauthorizedError, NotFoundError, ConflictError }
