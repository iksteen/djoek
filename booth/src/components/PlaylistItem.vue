<template>
  <div @click="$emit('activate')">
    <div
      v-if="!activated"
      class="my-3 d-flex align-center"
    >
      <div
        class="text-truncate mr-auto"
        v-text="title"
      />
      <div
        class="ml-1 grey--text text--lighten-1"
        v-text="duration"
      />
      <div
        v-if="rating !== null"
        class="ml-1 caption  grey--text text--lighten-1"
      >
        ({{ rating }})
      </div>
    </div>
    <div
      v-if="activated"
      class="my-3"
    >
      <item-card :item="item">
        <template v-slot:actions>
          <slot name="actions" />
        </template>
      </item-card>
    </div>
  </div>
</template>

<script>
  import ItemCard from './ItemCard'
  import { formatDuration, formatRating } from '../utils'

  export default {
    name: 'PlaylistItem',
    components: {
      ItemCard,
    },

    props: {
      item: Object,
      activated: Boolean,
    },

    computed: {
      title () {
        return this.item ? this.item.title : 'unknown'
      },
      duration () {
        return formatDuration(this.item ? this.item.duration : null)
      },
      rating () {
        return formatRating(this.item)
      },
    },
  }
</script>
