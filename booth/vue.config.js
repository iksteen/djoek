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
      '^/mpd.ogg$': {
        target: 'http://localhost:8001/mpd.ogg',
      },
      '^/player': {
        target: 'http://localhost:8002',
        pathRewrite: {
          '^/player': '',
        },
      },
    },
  },
  transpileDependencies: ['vuetify'],
}
