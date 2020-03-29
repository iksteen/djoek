import Vue from 'vue'
import Vuex from 'vuex'
import { getInstance as getApiInstance } from '../plugins/api'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    currentSong: null,
    nextSong: null,
    playlist: [],
    updateInterval: null,
    connected: false,
  },
  mutations: {
    UPDATE_STATUS: (state, { currentSong, nextSong }) => {
      state.currentSong = currentSong
      state.nextSong = nextSong
    },
    UPDATE_PLAYLIST: (state, playlist) => {
      state.playlist = playlist
    },
    SOCKET_ONOPEN: (state, event) => {
      state.connected = true
    },
    SOCKET_ONCLOSE: (state) => {
      state.connected = false
    },
    SOCKET_ONERROR: () => {},
    SOCKET_RECONNECT: () => {},
  },
  actions: {
    UPDATE_STATUS: async context => {
      const status = await getApiInstance().getStatus()
      context.commit('UPDATE_STATUS', status)
    },
    UPDATE_PLAYLIST: async ({ commit }) => {
      const playlist = await getApiInstance().getPlaylist()
      commit('UPDATE_PLAYLIST', playlist)
    },
    EVENT: async ({ dispatch }, { event }) => {
      if (event === 'update') {
        await Promise.all([
          dispatch('UPDATE_STATUS'),
          dispatch('UPDATE_PLAYLIST'),
        ])
      }
    },
  },
  modules: {},
})

export default store
