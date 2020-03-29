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
    <v-divider class="mb-4" />

    <v-subheader class="px-0">
      Now playing
    </v-subheader>
    <playlist-item
      :item="currentSong"
      :activated="isActive(currentSong)"
      @activate="toggleActive(currentSong)"
    />
    <v-subheader class="px-0">
      Up next
    </v-subheader>
    <playlist-item
      v-for="(item, i) in fullPlaylist.slice(1)"
      :key="i"
      :item="item"
      :activated="isActive(item)"
      @activate="toggleActive(item)"
    />
  </div>
</template>

<script>
  import { mapGetters, mapState } from 'vuex'
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
        active: null,
      }
    },
    computed: {
      ...mapState(['currentSong']),
      ...mapGetters(['fullPlaylist']),
    },
    watch: {
      fullPlaylist (playlist) {
        if (this.active !== null && !playlist.reduce(
          (result, item) => (result || item.externalId === this.active),
          false,
        )) {
          this.active = null
        }
      },
    },
    methods: {
      toggleActive (song) {
        if (song === null || song.externalId === this.active) {
          this.active = null
        } else {
          this.active = song.externalId
        }
      },
      isActive (song) {
        return song !== null && song.externalId === this.active
      },
    },
  }
</script>
