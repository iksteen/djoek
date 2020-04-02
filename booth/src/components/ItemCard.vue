<template>
  <v-card
    class="mx-auto"
    outlined
    :disabled="disabled"
    :loading="loading"
  >
    <v-card-text
      class="subtitle-1"
    >
      <div class="d-flex align-center">
        <div
          class="white--text"
          v-text="item.title"
        />
        <div
          class="ml-auto"
          v-text="duration"
        />
        <div
          v-if="rating !== null"
          class="pl-1 caption"
        >
          ({{ rating }})
        </div>
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
      <slot name="actions" />
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
</template>

<script>
  import { formatDuration, formatRating } from '../utils'

  export default {
    name: 'ItemCard',

    props: {
      item: Object,
      disabled: Boolean,
      loading: Boolean,
    },

    computed: {
      duration () {
        return formatDuration(this.item.duration)
      },

      rating () {
        return formatRating(this.item)
      },
    },

    methods: {
      preview () {
        window.open(this.item.previewUrl, '_blank', 'noopener,noreferrer')
      },
    },
  }
</script>
