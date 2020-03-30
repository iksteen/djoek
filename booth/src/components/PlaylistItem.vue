<template>
  <div @click="$emit('activate')">
    <div
      v-if="!activated"
      class="py-3 d-flex align-center"
    >
      <div
        class="text-truncate"
        v-text="title"
      />
      <div
        class="pl-1 ml-auto grey--text text--lighten-1"
        v-text="duration"
      />
      <div
        v-if="rating !== null"
        class="pl-1 caption  grey--text text--lighten-1"
      >
        ({{ rating }})
      </div>
    </div>
    <div
      v-if="activated"
      class="mt-3"
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
        return this.$api.formatDuration(this.item ? this.item.duration : null)
      },
      rating () {
        if (this.item === null || this.item.upvotes === null || this.item.downvotes === null) {
          return null
        }
        const rating = this.item.upvotes - this.item.downvotes
        return (rating > 0 ? '+' : '') + rating
      },
    },
  }
</script>
