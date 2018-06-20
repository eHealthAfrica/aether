# Frontend assets

Frontend assets include JS, CSS, and fonts. They are all handled by webpack.

Frontend assets are mounted on the pages via the
[django-webpack-loader](https://github.com/owais/django-webpack-loader).


## Build


### The 2 builds, server and prod

* There is a file with all the apps list: `webpack.apps.js`.

* There are three webpack configuration files:

  - `webpack.common.js`  -- contains the common features to build the webpack files.
  - `webpack.server.js`  -- starts the server in port `3000` with HOT reloading.
  - `webpack.prod.js`    -- compiles the files to be used in the Django app.

* The `start_webpack` entry point starts a webpack development server (port 3000),
  that watches assets, rebuilds and does hot reloading of JS Components.

  ```bash
  docker-compose up webpack
  ```


### CSS Build

The CSS build is separate, and can contain both `.sass` and `.css` files.
They spit out a webpack build called `styles.css`.


### JS Build

Each page has their own JS entry point (needs to be defined in `webpack.apps.js`).
On top of that, they load a common chunk, containing `jquery`, `bootstrap` and other
stuff that the `webpack common chunk` plugin finds is shared between the apps.


## JS Unit Testing and linting

The CSS style is analyzed by
[Sass Lint](https://github.com/sasstools/sass-lint).

The Javascript style is analyzed by
[Standard JS](https://github.com/feross/standard/>).

The Javascript code is tested using
[Jest](https://facebook.github.io/jest/docs/en/getting-started.html)
and [Enzyme](http://airbnb.io/enzyme/).

```bash
# all tests
docker-compose run ui eval npm run test

# by type
docker-compose run ui eval npm run test-lint-sass
docker-compose run ui eval npm run test-lint-js
docker-compose run ui eval npm run test-js

# in case you need to check `console.log` messages
docker-compose run ui eval npm run test-js-verbose
```


## Adding new libraries in package.json

Unfortunately, for now you need to rebuild the container after upgrading
or adding dependencies in `package.json`.

```bash
docker-compose kill ui
docker-compose up --build ui
```


## Naming/Coding conventions

There are a couple of naming/coding conventions followed by the React Components:

* Style linting rules defined in file `/conf/extras/sass-lint.yml`.

* Javascript linting rules defined by [Standard JS](https://github.com/feross/standard/>).

* The file name will match the default Component name defined inside,
  it might be the case that auxiliary components are also defined in the same file.

* Names are self-explanatory like `RefreshingSpinner`, `ProjectList`,
  `constants` and so on.

* Coding conventions:

  - Javascript:
    - component names use title case (`TitleCase`)
    - utility files kebab case (`kebab-case`)
    - methods and variables camel case (`camelCase`)

  - Python:
    - file names, methods and variables snake case (`snake_case`)
    - class names use title case (`TitleCase`)

* Meaningful suffixes:

  - `Container` indicates that the component will fetch data from the server.
  - `List` indicates that the data is a list and is displayed as a table or list.
  - `Form` indicates that a form will be displayed.

* Test files are kept in the same folder and the name is `MyComponent.spec.jsx`.

* App "agnostic" components are kept in folder `apps/components`

* App "agnostic" methods are kept in folder `apps/utils`

* **Comments are warmly welcome!!!**
