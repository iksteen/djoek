<template>
  <div>
    <div class="d-flex">
      <div class="display-1">
        Playlist
      </div>
      <div class="ml-auto d-flex">
        <stream-caster />
        <stream-player />
      </div>
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
  import StreamCaster from './StreamCaster'
  import StreamPlayer from './StreamPlayer'

  export default {
    name: 'Playlist',
    components: {
      PlaylistItem,
      StreamCaster,
      StreamPlayer,
    },
    data () {
      return {
        updateHandle: null,
      }
    },
    computed: {
      ...mapState(['currentSong', 'nextSong', 'playlist']),
    },
    created () {
      this.update()
    },
    beforeDestroy () {
      if (this.updateHandle !== null) {
        clearTimeout(this.updateHandle)
      }
    },
    methods: {
      async update () {
        this.updateHandle = null
        try {
          await Promise.all([
            this.updateStatus(),
            this.updatePlaylist(),
          ])
        } finally {
          this.updateHandle = setTimeout(
            () => this.update(),
            1000,
          )
        }
      },

      ...mapActions({
        updateStatus: 'UPDATE_STATUS',
        updatePlaylist: 'UPDATE_PLAYLIST',
      }),
    },
  }
</script>
