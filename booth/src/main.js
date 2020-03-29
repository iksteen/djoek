import Vue from 'vue'
import VueNativeSock from 'vue-native-websocket'
import App from './App.vue'
import store from './store'

import { Auth0Plugin } from './plugins/auth'

import { ApiPlugin } from './plugins/api'
import vuetify from './plugins/vuetify'

fetch('./auth-config.json')
  .then(response => response.json())
  .then(authConfig => {
    Vue.use(Auth0Plugin, authConfig)
    Vue.use(ApiPlugin)

    const wsOrigin = window.location.origin.replace(/^http(?=s?:\/\/)/, 'ws')
    Vue.use(VueNativeSock, `${wsOrigin}/api/events`, {
      store: store,
      format: 'json',
      reconnection: true,
      reconnectionDelay: 5000,
    })

    Vue.config.productionTip = false

    new Vue({
      store,
      vuetify,
      render: h => h(App),
    }).$mount('#app')
  })
