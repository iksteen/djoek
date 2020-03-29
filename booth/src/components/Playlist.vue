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
    <playlist-item :item="currentSong" />
    <v-subheader class="px-0">
      Up next
    </v-subheader>
    <playlist-item :item="nextSong" />
    <playlist-item
      v-for="(item, i) in playlist"
      :key="i"
      :item="item"
    />
  </div>
</template>

<script>
  import { mapState } from 'vuex'
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
    computed: {
      ...mapState(['currentSong', 'nextSong', 'playlist']),
    },
  }
</script>
