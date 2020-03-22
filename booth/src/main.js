import Vue from 'vue'
import App from './App.vue'
import store from './store'

import { domain, clientId, audience } from '../../auth-config.json'

import { Auth0Plugin } from './plugins/auth'

import { ApiPlugin } from './plugins/api'
import vuetify from './plugins/vuetify'
Vue.use(Auth0Plugin, {
  domain,
  clientId,
  audience,
})
Vue.use(ApiPlugin)

Vue.config.productionTip = false

new Vue({
  store,
  vuetify,
  render: h => h(App),
}).$mount('#app')
