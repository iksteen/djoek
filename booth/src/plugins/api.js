import Vue from 'vue'
import Axios from 'axios'
import { getInstance as getAuth0Instance } from './auth'

let instance

export const getInstance = () => instance

function transformItemSchema (song) {
  if (song === null) {
    return null
  }
  const { title, duration, external_id: externalId, preview_url: previewUrl, username, upvotes, downvotes } = song
  return {
    title,
    duration,
    externalId,
    previewUrl,
    username,
    upvotes,
    downvotes,
  }
}

const useApi = () => {
  if (instance) return instance

  instance = new Vue({
    methods: {
      async token () {
        return await getAuth0Instance().getTokenSilently()
      },

      async authRequest (method, url, ...args) {
        const token = await this.token()
        const config = {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
        return await Axios[method](url, ...(args || []), config)
      },

      async getStatus () {
        const {
          data: { current_song: currentSong, next_song: nextSong },
        } = await this.authRequest('get', '/api/')
        return {
          currentSong: transformItemSchema(currentSong),
          nextSong: transformItemSchema(nextSong),
        }
      },

      async getPlaylist () {
        const { data } = await this.authRequest('get', '/api/playlist/')
        return data.map(transformItemSchema)
      },

      async download (externalId, enqueue = true) {
        await this.authRequest('post', '/api/library/', {
          external_id: externalId,
          enqueue,
        })
      },

      async search (provider, query) {
        const { data } = await this.authRequest('post', '/api/search/', {
          q: query,
          provider,
        })
        return data.map(transformItemSchema)
      },

      async vote (direction) {
        await this.authRequest('post', `/api/current/vote/${direction}`, null)
      },

      async claim () {
        await this.authRequest('post', '/api/current/user', null)
      },
    },
  })

  return instance
}

export const ApiPlugin = {
  install (Vue, options) {
    Vue.prototype.$api = useApi(options)
  },
}
