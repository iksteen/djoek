<template>
  <div>
    <h3>Search:</h3>
    <input
      type="text"
      v-model="query"
      ref="query"
      @keyup.enter="search('youtube', query)"
    />
    &nbsp;
    <button @click="search('youtube', query)">Search YouTube</button>
    <div v-if="lastQuery">
      <h3 v-if="lastQuery">Results for {{ lastQuery }}:</h3>
      <ul>
        <li v-for="result in results" :key="result.externalId">
          {{ result.title }} -
          <a href="#" @click.prevent="download(result.externalId, true)">
            Add
          </a>
          <span v-if="provider !== 'local'">
            -
            <a href="#" @click.prevent="download(result.externalId, false)">
              Download
            </a>
          </span>
          <span v-if="result.previewUrl">
            -
            <a
              :href="result.previewUrl"
              rel="noopener noreferrer"
              target="_blank"
            >
              Preview
            </a>
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { mapActions } from "vuex";

export default {
  name: "Search",
  data() {
    return {
      query: "",
      lastQuery: "",
      results: [],
      provider: null,
      searchTimeout: null,
      pendingQuery: null
    };
  },
  beforeDestroy() {
    this.cancelSearchTimeout();
  },
  watch: {
    query(query) {
      this.cancelSearchTimeout();

      if (!query) {
        this.results = [];
        this.lastQuery = "";
        return;
      }

      this.searchTimeout = setTimeout(
        () => this.search("local", this.query),
        100
      );
    }
  },
  methods: {
    cancelSearchTimeout() {
      if (this.searchTimeout !== null) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = null;
      }
      this.pendingSearch = null;
    },

    async search(provider, q) {
      this.pendingSearch = [provider, q];

      const results = await this.$api.search(provider, q);

      if (
        !this.pendingSearch ||
        this.pendingSearch[0] !== provider ||
        this.pendingSearch[1] !== q
      ) {
        return;
      }
      this.pendingSearch = null;

      this.results = results;
      this.lastQuery = q;
      this.provider = provider;
    },

    reset() {
      this.query = "";
      this.lastQuery = "";
      this.results = [];
      this.$refs.query.focus();
    },

    async download(externalId, enqueue) {
      this.reset();
      await this.$api.download(externalId, enqueue);
      this.updateStatus();
      this.updatePlaylist();
    },

    ...mapActions({
      updateStatus: "UPDATE_STATUS",
      updatePlaylist: "UPDATE_PLAYLIST"
    })
  }
};
</script>
