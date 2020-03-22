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
    <div v-if="lastQuery">
      <div
        class="title"
        v-if="lastQuery"
      >
        Results for {{ lastQuery }}:
      </div>
      <search-result
        v-for="(result, i) in results"
        :key="i"
        :title="result.title"
        :provider="provider"
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
        provider: null,
        searchTimeout: null,
        pendingQuery: null,
      }
    },
    watch: {
      query (query) {
        this.cancelSearchTimeout()

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

        this.results = results
        this.lastQuery = q
        this.provider = provider
      },

      reset () {
        this.query = ''
        this.lastQuery = ''
        this.results = []
        this.$refs.query.focus()
      },

      async download (externalId, enqueue) {
        this.reset()
        await this.$api.download(externalId, enqueue)
        this.updateStatus()
        this.updatePlaylist()
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
