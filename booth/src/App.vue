<template>
  <div v-if="!$auth.loading">
    <button v-if="!$auth.isAuthenticated" @click="login">Log in</button>
    <Booth v-if="$auth.isAuthenticated" />
  </div>
</template>

<script>
import Booth from "./components/Booth.vue";

export default {
  name: "App",
  components: {
    Booth
  },
  methods: {
    login() {
      this.$auth.loginWithRedirect();
    }
  }
};
</script>

<style>
body {
  background-color: black;
  margin: 0;
  padding: 0;
}

* {
  color: white;
  box-sizing: border-box;
}

input,
button {
  color: black;
}
</style>
