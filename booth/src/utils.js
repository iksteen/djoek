export function formatDuration (duration) {
  if (duration === null) {
    return '-:--'
  }

  const minutes = Math.trunc(duration / 60)
  const seconds = Math.trunc(duration % 60)
  return `${minutes}:${`00${seconds}`.slice(-2)}`
}

export function formatRating (song) {
  if (song === null || song.upvotes === null || song.downvotes === null) {
    return null
  }
  const { upvotes, downvotes } = song
  if (upvotes === 0 && downvotes === 0) {
    return '\u2013'
  }
  const rating = upvotes - downvotes
  return rating > 0 ? `+${rating}` : `${rating}`
}
