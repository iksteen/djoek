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
    <div v-if="activated">
      <v-card
        class="mx-auto my-3"
        outlined
      >
        <v-card-text
          class="subtitle-1"
        >
          <div class="d-flex">
            <div
              class="white--text"
              v-text="item.title"
            />
            <div
              class="ml-auto"
              v-text="$api.formatDuration(item.duration)"
            />
          </div>
          <div
            v-if="item.username"
            class="caption font-italic font-weight-light"
          >
            First added by {{ item.username }}.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <v-btn
                icon
                v-on="on"
                @click.stop="preview"
              >
                <v-icon>mdi-open-in-new</v-icon>
              </v-btn>
            </template>
            <span>Preview</span>
          </v-tooltip>
        </v-card-actions>
      </v-card>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'PlaylistItem',
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

    methods: {
      preview () {
        window.open(this.item.previewUrl, '_blank', 'noopener,noreferrer')
      },
    },
  }
</script>
