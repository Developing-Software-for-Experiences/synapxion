<!-- App.vue -->
<template>
  <BApp>
    <header>
      <NavBar />
    </header>
    <!-- Your application content -->
    <main class="container-sm">
      <router-view />
    </main>
    <footer>
      <FootBar />
    </footer>
  </BApp>
</template>

<script setup lang="ts">
import {BApp} from 'bootstrap-vue-next'
import NavBar from './views/navBar.vue';
import FootBar from './views/footBar.vue';
</script>

<style>
  main {
    width: 100%;
    height: fit-content;
  }
</style>
