<template>
  <div>
    <Status />
    <hr />
    <Playlist />
  </div>
</template>

<script>
import Status from "./Status";
import Playlist from "./Playlist";
import { mapActions } from "vuex";

export default {
  name: "Console",
  components: {
    Playlist,
    Status
  },
  data() {
    return {
      updateHandle: null
    };
  },
  mounted() {
    this.update();
    this.updateHandle = setInterval(this.update, 1000);
  },
  destroyed() {
    if (this.updateHandle !== null) {
      clearInterval(self.updateHandle);
    }
  },
  methods: {
    update() {
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
