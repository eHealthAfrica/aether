import superagent from 'superagent'
import cookie from 'react-cookie'

const methods = ['get', 'post', 'put', 'patch', 'del']

export default class ApiClient {
  constructor (req) {
    methods.forEach(method => {
      this[method] = (path, header, { params, data } = {}) =>
        new Promise((resolve, reject) => {
          const request = superagent[method](path)

          if (header) {
            request.set('Accept', header)
          }
          if (cookie.load('accessToken')) {
            request.set('Authorization', `Bearer ${cookie.load('accessToken')}`)
          }
          if (params) {
            request.query(params)
          }

          if (req && req.get('cookie')) {
            request.set('cookie', req.get('cookie'))
          }

          if (data) {
            request.send(data)
          }
          request.end((err, { body } = {}) => (err ? reject(body || err) : resolve(body)))
        })
    })
  }
}
