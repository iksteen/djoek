<template>
  <div class="status">
    <h3>Player status:</h3>
    <div class="song">
      Current song:
      <span class="song-title">{{ currentSong }}</span>
    </div>
    <div class="song">
      Next song:
      <span class="song-title">{{ nextSong }}</span>
    </div>
  </div>
</template>

<script>
import { mapState } from "vuex";

export default {
  name: "Status",
  computed: {
    ...mapState(["currentSong", "nextSong"])
  }
};
</script>
