<template>
  <div @click="$emit('activate')">
    <div
      v-if="!activated"
      class="py-3 d-flex"
    >
      <div
        class="text-truncate"
        v-text="title"
      />
      <div
        class="pl-1 ml-auto grey--text text--lighten-1"
        v-text="duration"
      />
    </div>
    <div
      v-if="activated"
      class="mt-3"
    >
      <item-card :item="item" />
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
    },
  }
</script>
