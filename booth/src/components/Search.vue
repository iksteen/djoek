<template>
  <div>
    <div class="display-1">
      Search
    </div>
    <v-divider />
    <v-text-field
      ref="query"
      v-model="query"
      @keyup.enter="search('youtube', query)"
    >
      <template v-slot:append-outer>
        <search-button
          icon="mdi-youtube"
          tooltip="Search on YouTube"
          @click="search('youtube', query)"
        />
        <search-button
          icon="mdi-soundcloud"
          tooltip="Search on SoundCloud"
          @click="search('soundcloud', query)"
        />
      </template>
    </v-text-field>
    &nbsp;
    <div
      v-if="lastQuery && !results.length"
      class="subtitle-1"
    >
      <em>No results for {{ lastQuery }}.</em>
    </div>
    <v-alert
      v-if="error"
      type="error"
    >
      Failed to download the song: {{ error }}
    </v-alert>

    <div v-if="lastQuery && results.length > 0">
      <div class="subtitle-1">
        Results for {{ lastQuery }}:
      </div>
      <search-result
        v-for="result in results"
        :key="`${result.provider}:${result.externalId}`"
        :title="result.title"
        :provider="result.provider"
        :duration="result.duration"
        :disabled="!!downloading"
        :loading="downloading === result.externalId"
        @download="download(result.externalId, false)"
        @enqueue="download(result.externalId, true)"
        @preview="preview(result.previewUrl)"
      />
    </div>
  </div>
</template>

<script>
  import { VTextField } from 'vuetify/lib'
  import { mapActions } from 'vuex'
  import SearchButton from './SearchButton'
  import SearchResult from './SearchResult'

  export default {
    name: 'Search',
    components: {
      SearchResult,
      SearchButton,
      VTextField,
    },
    data () {
      return {
        query: '',
        lastQuery: '',
        results: [],
        searchTimeout: null,
        pendingQuery: null,
        downloading: null,
        error: null,
      }
    },
    watch: {
      query (query) {
        this.cancelSearchTimeout()
        this.downloading = null
        this.error = null

        if (!query) {
          this.results = []
          this.lastQuery = ''
          return
        }

        this.searchTimeout = setTimeout(
          () => this.search('local', this.query),
          100,
        )
      },
    },
    mounted () {
      this.$refs.query.focus()
    },
    beforeDestroy () {
      this.cancelSearchTimeout()
    },
    methods: {
      cancelSearchTimeout () {
        if (this.searchTimeout !== null) {
          clearTimeout(this.searchTimeout)
          this.searchTimeout = null
        }
        this.pendingSearch = null
      },

      async search (provider, q) {
        if (!q) {
          return
        }

        this.pendingSearch = [provider, q]

        const results = await this.$api.search(provider, q)

        if (
          !this.pendingSearch ||
          this.pendingSearch[0] !== provider ||
          this.pendingSearch[1] !== q
        ) {
          return
        }
        this.pendingSearch = null

        this.results = results.map(result => ({
          ...result,
          provider,
        }))
        this.lastQuery = q
      },

      reset () {
        this.query = ''
        this.lastQuery = ''
        this.results = []
        this.downloading = null
        this.error = null
        this.$refs.query.focus()
      },

      async download (externalId, enqueue) {
        this.error = null
        this.downloading = externalId
        try {
          await this.$api.download(externalId, enqueue)
          this.reset()
          this.updateStatus()
          this.updatePlaylist()
        } catch (e) {
          this.downloading = null
          this.error = e
        }
      },

      preview (url) {
        window.open(url, '_blank', 'noopener,noreferrer')
      },

      ...mapActions({
        updateStatus: 'UPDATE_STATUS',
        updatePlaylist: 'UPDATE_PLAYLIST',
      }),
    },
  }
</script>
