<template>
  <v-app v-if="!$auth.loading">
    <v-content>
      <button
        v-if="!$auth.isAuthenticated"
        @click="login"
      >
        Log in
      </button>
      <booth v-if="$auth.isAuthenticated" />
    </v-content>
  </v-app>
</template>

<script>
  import Booth from './components/Booth'

  export default {
    name: 'App',

    components: {
      Booth,
    },

    methods: {
      login () {
        this.$auth.loginWithRedirect()
      },
    },
  }
</script>
