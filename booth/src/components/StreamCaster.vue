<template>
  <v-btn
    icon
    :hidden="!available"
    @click="toggle()"
  >
    <v-icon
      :color="color"
      v-text="icon"
    />
  </v-btn>
</template>

<script>
  import { Castjs } from '../vendor/cast'

  const cc = new Castjs()

  export default {
    name: 'StreamCaster',

    data () {
      return {
        available: false,
        connected: false,
      }
    },

    computed: {
      color () {
        return this.connected ? 'blue' : 'grey'
      },
      icon () {
        return this.connected ? 'mdi-cast-connected' : 'mdi-cast'
      },
    },

    mounted () {
      this.available = cc.available
      this.connected = !!cc.session
      cc.on('any', () => {
        this.available = cc.available
        this.connected = !!cc.session
      })
    },

    beforeDestroy () {
      cc.off()
    },

    methods: {
      toggle () {
        if (!this.connected) {
          cc.cast(`${location.origin}/mpd.ogg`, {
            title: 'Djoek Radio',
            muted: false,
            paused: false,
          })
        } else {
          cc.disconnect()
        }
      },
    },
  }
</script>
