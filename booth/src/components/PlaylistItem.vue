<template>
  <v-list-item>
    <v-list-item-content>
      <v-list-item-title v-text="title" />
    </v-list-item-content>
  </v-list-item>
</template>

<script>
  export default {
    name: 'PlaylistItem',
    props: {
      title: String,
    },
  }
</script>
