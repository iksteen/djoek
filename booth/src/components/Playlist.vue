<template>
  <div>
    <div class="display-1">
      Playlist
    </div>
    <v-divider />

    <v-list class="mt-4">
      <v-subheader>Now playing</v-subheader>
      <playlist-item :title="currentSong" />
      <v-subheader>Up next</v-subheader>
      <playlist-item :title="nextSong" />
      <playlist-item
        v-for="(item, i) in playlist"
        :key="i"
        :title="item.title"
      />
    </v-list>
  </div>
</template>

<script>
  import { mapActions, mapState } from 'vuex'
  import PlaylistItem from './PlaylistItem'

  export default {
    name: 'Playlist',
    components: { PlaylistItem },
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
