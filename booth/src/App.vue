<template>
  <v-app v-if="!$auth.loading">
    <v-content>
      <button
        v-if="!isAuthenticated"
        @click="login"
      >
        Log in
      </button>
      <booth v-if="isAuthenticated" />
    </v-content>
  </v-app>
</template>

<script>
  import Booth from './components/Booth'
  import { mapActions, mapState } from 'vuex'

  export default {
    name: 'App',

    components: {
      Booth,
    },

    data () {
      return {
        updateHandle: null,
      }
    },

    computed: {
      isAuthenticated () {
        return this.$auth.isAuthenticated
      },

      ...mapState(['connected']),
    },

    watch: {
      connected () {
        this.update()
      },

      isAuthenticated (authenticated) {
        if (authenticated) {
          this.update()
        }
      },
    },

    methods: {
      login () {
        this.$auth.loginWithRedirect()
      },

      async update () {
        if (this.updateHandle !== null) {
          clearTimeout(this.updateHandle)
          this.updateHandle = null
        }

        try {
          if (!this.isAuthenticated) {
            return
          }

          await Promise.all([
            this.updateStatus(),
            this.updatePlaylist(),
          ])
        } finally {
          if (!this.connected) {
            this.updateHandle = setTimeout(
              () => this.update(),
              5000,
            )
          }
        }
      },

      ...mapActions({
        updateStatus: 'UPDATE_STATUS',
        updatePlaylist: 'UPDATE_PLAYLIST',
      }),
    },
  }
</script>
