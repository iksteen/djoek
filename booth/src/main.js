import Vue from "vue";
import App from "./App.vue";
import store from "./store";

import { domain, clientId, audience } from "../../auth-config.json";

import { Auth0Plugin } from "./auth";
Vue.use(Auth0Plugin, {
  domain,
  clientId,
  audience
});

import { ApiPlugin } from "./api";
Vue.use(ApiPlugin);

Vue.config.productionTip = false;

new Vue({
  store,
  render: h => h(App)
}).$mount("#app");
