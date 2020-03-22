<template>
  <div>
    <h3>Search:</h3>
    <input
      type="text"
      v-model="query"
      ref="query"
      @keyup.enter="search(query, true)"
    />
    &nbsp;
    <button @click="search(query, true)">Search YouTube</button>
    <div v-if="lastQuery">
      <h3 v-if="lastQuery">Results for {{ lastQuery }}:</h3>
      <ul>
        <li v-for="result in results" :key="result.videoId">
          {{ result.title }} -
          <a href="#" @click.prevent="download(result.videoId, true)">
            Add
          </a>
          -
          <span v-if="externalSearch">
            <a href="#" @click.prevent="download(result.videoId, false)">
              Download
            </a>
            -
          </span>
          <a
            :href="`https://youtu.be/${result.videoId}`"
            rel="noopener noreferrer"
            target="_blank"
          >
            [YouTube]
          </a>
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
      externalSearch: false,
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

      this.searchTimeout = setTimeout(() => this.search(this.query), 100);
    }
  },
  methods: {
    cancelSearchTimeout() {
      if (this.searchTimeout !== null) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = null;
      }
    },

    async search(q, external = false) {
      this.pendingSearch = [q, external];

      const { results, external: externalSearch } = await this.$api.search(
        q,
        external
      );

      if (
        !this.pendingSearch ||
        this.pendingSearch[0] !== q ||
        this.pendingSearch[1] !== external
      ) {
        return;
      }
      this.pendingSearch = null;

      this.results = results.map(({ title, video_id }) => ({
        title,
        videoId: video_id
      }));
      this.lastQuery = q;
      this.externalSearch = externalSearch;
    },

    reset() {
      this.query = "";
      this.lastQuery = "";
      this.results = [];
      this.$refs.query.focus();
    },

    async download(videoId, enqueue) {
      this.reset();
      await this.$api.download(videoId, enqueue);
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
