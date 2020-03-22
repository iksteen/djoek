<template>
  <v-container fluid>
    <v-row>
      <v-col
        cols="12"
        md="6"
        order="2"
        order-md="1"
      >
        <search />
      </v-col>
      <v-col
        cols="12"
        md="6"
        order="1"
        order-md="2"
      >
        <playlist />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import Search from './Search'
  import Playlist from './Playlist'

  export default {
    name: 'Booth',
    components: {
      Search,
      Playlist,
    },
  }
</script>
