<!-- App.vue -->
<template>
  <BApp>
    <header>
      <NavBar />
    </header>
    <!-- Your application content -->
    <main>
      <router-view />
    </main>
    <footer>
      <FootBar />
    </footer>
  </BApp>
</template>

<script setup lang="ts">
import { BApp } from 'bootstrap-vue-next'
import NavBar from './views/navBar.vue'
import FootBar from './views/footBar.vue'
</script>

<style>
main {
  width: 100%;
  height: fit-content;
}

.navbar {
  background-color: #fa4f84;
  font-size: 18px;
}

.navbar .navbar-brand,
.navbar .nav-link {
  color: #ffffff !important;

}

.navbar .navitems .nav-link {
  color: #ffffff !important;
}

.navbar .dropdown-item {
  color: black;
}

.navbar .btn {
  color: #ffffff;
  border-color: #ffffff;
}

</style>
