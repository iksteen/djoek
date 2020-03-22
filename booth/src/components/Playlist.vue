<template>
  <div>
    <h3>Playlist</h3>
    <v-divider />

    <ul class="playlist">
      <li>{{ currentSong || "unknown" }}</li>
      <li>{{ nextSong || "unkown" }}</li>
      <li
        v-for="item in playlist"
        :key="item.title"
      >
        {{ item.title }}
      </li>
    </ul>
  </div>
</template>

<script>
  import { mapActions, mapState } from 'vuex'

  export default {
    name: 'Playlist',
    data () {
      return {
        updateHandle: null,
      }
    },
    computed: {
      ...mapState(['currentSong', 'nextSong', 'playlist']),
    },
    mounted () {
      this.update()
      this.updateHandle = setInterval(this.update, 1000)
    },
    destroyed () {
      if (this.updateHandle !== null) {
        clearInterval(self.updateHandle)
      }
    },
    methods: {
      update () {
        this.updateStatus()
        this.updatePlaylist()
      },

      ...mapActions({
        updateStatus: 'UPDATE_STATUS',
        updatePlaylist: 'UPDATE_PLAYLIST',
      }),
    },
  }
</script>
