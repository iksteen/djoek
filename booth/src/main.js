import Vue from 'vue'
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

    Vue.config.productionTip = false

    new Vue({
      store,
      vuetify,
      render: h => h(App),
    }).$mount('#app')
  })
