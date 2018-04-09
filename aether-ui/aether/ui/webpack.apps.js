// The list of current apps that DO need Hot Module Replacement in development mode
const apps = [
  {
    name: 'styles',
    path: './assets/css/index.scss'
  },
  {
    name: 'home',
    path: './assets/apps/home'
  }
]

const buildEntries = (hmr) => {
  const list = {
    // the apps that DO NOT need Hot Module Replacement in development mode
    'common': [ 'jquery', 'popper.js', 'bootstrap' ],
    'html5shiv': 'html5shiv'
  }

  apps.forEach(app => {
    list[app.name] = (hmr ? [ ...hmr, app.path ] : app.path)
  })

  return list
}

module.exports = buildEntries
