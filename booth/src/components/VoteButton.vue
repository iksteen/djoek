<template>
  <v-tooltip bottom>
    <template v-slot:activator="{ on }">
      <v-btn
        text
        v-on="on"
        @click.stop="$emit('click')"
      >
        <v-icon>
          mdi-thumb-{{ direction }}
        </v-icon>
        <span class="ml-1">
          ({{ votes }})
        </span>
      </v-btn>
    </template>
    <span>Vote {{ direction }}</span>
  </v-tooltip>
</template>

<script>
  export default {
    name: 'VoteButton',
    props: {
      votes: Number,
      direction: String,
    },
  }
</script>
