import Vue from 'vue'
import Vuex from 'vuex'
import { getInstance as getApiInstance } from '../plugins/api'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    currentSong: null,
    nextSong: null,
    playlist: [],
  },
  mutations: {
    UPDATE_STATUS: (state, { currentSong, nextSong }) => {
      state.currentSong = currentSong
      state.nextSong = nextSong
    },
    UPDATE_PLAYLIST: (state, playlist) => {
      state.playlist = playlist
    },
  },
  actions: {
    UPDATE_STATUS: async context => {
      const status = await getApiInstance().getStatus()
      context.commit('UPDATE_STATUS', status)
    },
    UPDATE_PLAYLIST: async context => {
      const playlist = await getApiInstance().getPlaylist()
      context.commit('UPDATE_PLAYLIST', playlist)
    },
  },
  modules: {},
})
