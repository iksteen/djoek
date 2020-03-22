<template>
  <v-tooltip bottom>
    <template v-slot:activator="{ on }">
      <v-btn
        class="mx-2"
        outlined
        fab
        x-small
        v-on="on"
        @click="$emit('click')"
      >
        <v-icon>{{ icon }}</v-icon>
      </v-btn>
    </template>
    <span v-text="tooltip" />
  </v-tooltip>
</template>

<script>
  export default {
    name: 'SearchButton',
    props: {
      icon: String,
      tooltip: String,
    },
  }
</script>
