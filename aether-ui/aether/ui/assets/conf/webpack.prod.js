/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

var fs = require('fs')
var path = require('path')
var S3Plugin = require('webpack-s3-plugin')
var buildConfig = require('./webpack.common')
var GCSPlugin = require('webpack-google-cloud-storage-plugin')


function readFile (filename) {
  try {
    return fs.readFileSync(filename).toString().replace(/(\r\n|\n|\r)/gm, '')
  } catch (e) {
    return null
  }
}

function getCDNPlugin() {
    if (process.env.CDN_PLATFORM) {
        switch (process.env.CDN_PLATFORM) {
            case 's3':
                return [
                    new S3Plugin({
                        // s3Options are required
                        s3Options: {
                          accessKeyId: process.env.AWS_ACCESS_KEY_ID,
                          secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
                          region: process.env.AWS_S3_REGION_NAME
                        },
                        s3UploadOptions: {
                          Bucket: process.env.BUCKET_NAME
                        },
                        cdnizerOptions: {
                          defaultCDNBase: process.env.WEBPACK_URL
                        }
                      })
                ]

            case 'gcs':
                return [
                    new GCSPlugin({
                        directory: '/code/bundles',
                        include: ['.*\.(js|css)$'],
                        storageOptions: {
                          projectId: 'aether-test',
                          credentials: require(process.env.GOOGLE_APPLICATION_CREDENTIALS),
                        },
                        uploadOptions: {
                          bucketName: process.env.BUCKET_NAME,
                          makePublic: true,
                          resumable: true,
                          concurrency: 5,
                          destinationNameFn: file => path.basename(file.path)
                        },
                      }),
                ]
            default:
                return []
        }
    }
    return []
}

// read VERSION and REVISION files
// to identify files with current branch and commit hash
var version = readFile('/var/tmp/VERSION')
var revision = readFile('/var/tmp/REVISION')

var prefix = `[name]-${version || '0.0.0'}`

module.exports = buildConfig({
  production: true,
  stylesAsCss: true,
  jsFilename: `${prefix}-${revision || '[hash]'}.js`,
  cssFilename: `${prefix}-${revision || '[chunkhash]'}.css`,
  output: process.env.CDN_PLATFORM ? {
    // Tell django to use this URL to load packages
    // and not use STATIC_URL + bundle_name
    publicPath: process.env.WEBPACK_URL
  } : {},
  plugins: getCDNPlugin()
})
