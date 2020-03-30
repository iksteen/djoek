<template>
  <div class="mt-4">
    <item-card
      :item="item"
      :disabled="disabled"
      :loading="loading"
    >
      <template v-slot:actions>
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
          <span>Add to library</span>
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
      </template>
    </item-card>
  </div>
</template>

<script>
  import ItemCard from './ItemCard'

  export default {
    name: 'SearchResult',

    components: {
      ItemCard,
    },

    props: {
      provider: String,
      item: Object,
      disabled: Boolean,
      loading: Boolean,
    },
  }
</script>
