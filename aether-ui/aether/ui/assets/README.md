# Frontend assets

Frontend assets include JS, CSS, and fonts. They are all handled by webpack.

Frontend assets are mounted on the pages via the
[django-webpack-loader](https://github.com/owais/django-webpack-loader).

## Build

### The 2 builds, server and prod

* There is a file with all the apps list: `conf/webpack.apps.js`.

* There are three webpack configuration files:

  - `conf/webpack.common.js`  -- contains the common features to build the webpack files.
  - `conf/webpack.server.js`  -- starts the server in port `3004` with HOT reloading.
  - `conf/webpack.prod.js`    -- compiles the files to be used in the Django app.

* The `start_dev` entry point starts a webpack development server (port 3004),
  that watches assets, rebuilds and does hot reloading of JS Components and CSS files.

  ```bash
  docker-compose up ui-assets
  ```

### CSS Build

The CSS build is separate, and can contain both `.sass` and `.css` files.
They spit out a webpack build called `styles.css`.

### JS Build

Each page has their own JS entry point (needs to be defined in `webpack.apps.js`).
On top of that, they load a common chunk, containing `bootstrap`, `popper.js` and other
stuff that the `webpack common chunk` plugin finds is shared between the apps.
