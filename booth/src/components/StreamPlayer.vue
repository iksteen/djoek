<template>
  <div>
    <v-progress-circular
      v-if="loading"
      indeterminate
      size="24"
    />
    <v-btn
      v-if="!loading"
      icon
    >
      <v-icon
        @click="toggle()"
        v-text="icon"
      />
    </v-btn>
    <audio
      ref="stream"
      preload="none"
      @pause="state = 'paused'"
      @canplay="unmute()"
    />
  </div>
</template>

<script>
  export default {
    name: 'StreamPlayer',
    data () {
      return {
        state: 'paused',
      }
    },
    computed: {
      icon () {
        return {
          paused: 'mdi-play',
          playing: 'mdi-pause',
          failed: 'mdi-alert-circle',
        }[this.state]
      },
      loading () {
        return this.state === 'loading'
      },
    },
    methods: {
      unmute () {
        setTimeout(() => {
          const stream = this.$refs.stream
          stream.muted = false
          this.state = 'playing'
        }, 2000)
      },
      toggle () {
        const stream = this.$refs.stream

        if (this.state !== 'playing') {
          stream.src = '/mpd.ogg?' + Date.now()
          this.state = 'loading'
          this.$nextTick(() => {
            stream.muted = true
            stream.play().catch(e => {
              this.state = 'failed'
            })
          })
        } else {
          stream.pause()
        }
      },
    },
  }
</script>
