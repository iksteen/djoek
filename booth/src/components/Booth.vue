<template>
  <div class="container">
    <div class="item">
      <Search />
    </div>
    <div class="item">
      <Console />
    </div>
  </div>
</template>

<script>
import Console from "./Console";
import Search from "./Search";

export default {
  name: "Booth",
  components: {
    Console,
    Search
  }
};
</script>

<style scoped>
.container {
  position: absolute;
  width: 100%;
}

.item {
  padding: 10px;
  vertical-align: top;
  display: inline-block;
  width: 50%;
}
</style>
