const CopyPlugin = require('copy-webpack-plugin')

const authCopy = process.env.NODE_ENV !== 'production'
  ? [
    new CopyPlugin([{
      from: '../auth-config.json',
    }]),
  ]
  : []

module.exports = {
  publicPath: process.env.NODE_ENV === 'production'
    ? '/booth/'
    : '/',
  devServer: {
    proxy: {
      '^/api/': {
        target: 'http://localhost:8000',
        pathRewrite: {
          '^/api/': '/',
        },
      },
      '^/player': {
        target: 'http://localhost:8000',
      },
      '^/mpd.ogg$': {
        target: 'http://localhost:8001/mpd.ogg',
      },
    },
    writeToDisk: (filePath) => {
      return /^auth-config\.json$/.test(filePath)
    },
  },
  transpileDependencies: ['vuetify'],
  configureWebpack: {
    plugins: [
      ...authCopy,
    ],
  },
}
