<template>
  <Booth />
</template>

<script>
import Booth from "./components/Booth.vue";

export default {
  name: "App",
  components: {
    Booth
  }
};
</script>

<style>
body {
  background-color: black;
  margin: 0;
  padding: 0;
}

* {
  color: white;
  box-sizing: border-box;
}

input,
button {
  color: black;
}
</style>
