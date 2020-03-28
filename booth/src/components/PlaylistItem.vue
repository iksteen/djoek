<template>
  <div class="py-3 d-flex">
    <div
      class="text-truncate"
      v-text="title"
    />
    <div
      class="pl-1 ml-auto grey--text text--lighten-1"
      v-text="duration"
    />
  </div>
</template>

<script>
  export default {
    name: 'PlaylistItem',
    props: {
      item: Object,
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
