import Vue from "vue";
import Axios from "axios";
import { getInstance as getAuth0Instance } from "./auth";

let instance;

export const getInstance = () => instance;

const useApi = () => {
  if (instance) return instance;

  instance = new Vue({
    methods: {
      async token() {
        return await getAuth0Instance().getTokenSilently();
      },

      async authRequest(method, url, ...args) {
        const token = await this.token();
        const config = {
          headers: {
            Authorization: `Bearer ${token}`
          }
        };
        return await Axios[method].apply(Axios, [url, ...(args || []), config]);
      },

      async getStatus() {
        const {
          data: { current_song: currentSong, next_song: nextSong }
        } = await Axios.get("/api/");
        return { currentSong, nextSong };
      },

      async getPlaylist() {
        const { data } = await this.authRequest("get", "/api/playlist/");
        return data;
      },

      async download(videoId, enqueue = true) {
        await this.authRequest("post", "/api/library/", {
          video_id: videoId,
          enqueue
        });
      },

      async search(query, external = false) {
        const { data } = await this.authRequest("post", "/api/search/", {
          q: query,
          external
        });
        return data;
      }
    }
  });

  return instance;
};

export const ApiPlugin = {
  install(Vue, options) {
    Vue.prototype.$api = useApi(options);
  }
};
