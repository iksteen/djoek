<template>
  <div
    class="py-3 text-truncate"
    v-text="title"
  />
</template>

<script>
  export default {
    name: 'PlaylistItem',
    props: {
      title: String,
    },
  }
</script>
