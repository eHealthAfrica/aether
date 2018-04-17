import superagent from 'superagent'

const methods = ['get', 'post', 'put', 'patch', 'del']

export default class ApiClient {
  constructor (req) {
    methods.forEach(method => {
      this[method] = (path, header, { params, data } = {}) =>
        new Promise((resolve, reject) => {
          fetch(path, {
            body: JSON.stringify(data),
            method: method,
            headers: header
          })
          .then(res => {
            console.log(res)
            resolve(res)
          })
          .catch(err => reject(err))
          // const request = superagent[method](path)

          // if (header) {
          //   request.set('Accept', header)
          // }

          // if (params) {
          //   request.query(params)
          // }

          // if (data) {
          //   request.send(data)
          // }
          // request.end((err, res) => {
          //   console.log('REQ2', res)
          //   const accept = res.req.header['Accept']
          //   if (accept === 'application/json') {
          //     return res.json()
          //   }
          //   return err ? reject(res.body || err) : resolve(res.text())
          // })
        })
    })
  }
}
