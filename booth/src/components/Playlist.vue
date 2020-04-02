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
    >
      <template v-slot:actions>
        <v-tooltip
          v-if="currentSong !== null && currentSong.username === null"
          bottom
        >
          <template v-slot:activator="{ on }">
            <v-btn
              icon
              v-on="on"
              @click.stop="$api.claim()"
            >
              <v-icon>
                mdi-hand
              </v-icon>
            </v-btn>
          </template>
          <span>Claim as yours.</span>
        </v-tooltip>
        <vote-button
          direction="up"
          :votes="currentSong.upvotes"
          @click="$api.vote('up')"
        />
        <vote-button
          direction="down"
          :votes="currentSong.downvotes"
          @click="$api.vote('down')"
        />
      </template>
    </playlist-item>
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
  import VoteButton from './VoteButton'

  export default {
    name: 'Playlist',
    components: {
      VoteButton,
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
