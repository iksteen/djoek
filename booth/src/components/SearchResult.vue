<template>
  <v-card
    class="mx-auto mt-4"
    outlined
    :disabled="disabled"
    :loading="loading"
  >
    <v-card-text
      class="subtitle-1"
    >
      <div class="d-flex">
        <div v-text="title" />
        <div
          class="ml-auto"
          v-text="$api.formatDuration(duration)"
        />
      </div>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-tooltip bottom>
        <template v-slot:activator="{ on }">
          <v-btn
            v-if="provider !== 'local'"
            icon
            v-on="on"
            @click="$emit('download')"
          >
            <v-icon>mdi-cloud-download</v-icon>
          </v-btn>
        </template>
        <span>Download</span>
      </v-tooltip>
      <v-tooltip bottom>
        <template v-slot:activator="{ on }">
          <v-btn
            icon
            v-on="on"
            @click="$emit('enqueue')"
          >
            <v-icon>mdi-play</v-icon>
          </v-btn>
        </template>
        <span>Add to playlist</span>
      </v-tooltip>
      <v-tooltip bottom>
        <template v-slot:activator="{ on }">
          <v-btn
            icon
            v-on="on"
            @click="$emit('preview')"
          >
            <v-icon>mdi-open-in-new</v-icon>
          </v-btn>
        </template>
        <span>Preview</span>
      </v-tooltip>
    </v-card-actions>
  </v-card>
</template>

<script>
  export default {
    name: 'SearchResult',
    props: {
      title: String,
      duration: Number,
      provider: String,
      disabled: Boolean,
      loading: Boolean,
    },
  }
</script>
