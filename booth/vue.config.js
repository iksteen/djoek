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
  },
  transpileDependencies: ['vuetify'],
}
