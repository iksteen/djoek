import Vue from "vue";
import Vuex from "vuex";
import Axios from "axios";

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    currentSong: null,
    nextSong: null,
    playlist: []
  },
  mutations: {
    UPDATE_STATUS: (state, { currentSong, nextSong }) => {
      state.currentSong = currentSong;
      state.nextSong = nextSong;
    },
    UPDATE_PLAYLIST: (state, playlist) => {
      state.playlist = playlist;
    }
  },
  actions: {
    UPDATE_STATUS: async context => {
      const {
        data: { current_song: currentSong, next_song: nextSong }
      } = await Axios.get("/api/");
      context.commit("UPDATE_STATUS", { currentSong, nextSong });
    },
    UPDATE_PLAYLIST: async context => {
      const { data } = await Axios.get("/api/playlist/");
      context.commit("UPDATE_PLAYLIST", data);
    }
  },
  modules: {}
});
