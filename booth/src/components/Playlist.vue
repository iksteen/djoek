<template>
  <div class="playlist">
    <h3>Current playlist:</h3>

    <ul class="playlist" v-if="playlist.length > 0">
      <li v-for="item in playlist" :key="item.title">{{ item.title }}</li>
    </ul>

    <div v-else class="empty">
      Playlist is empty.
    </div>
  </div>
</template>

<script>
import { mapState } from "vuex";

export default {
  name: "Playlist",
  computed: {
    ...mapState(["playlist"])
  }
};
</script>
