<template>
  <BNavbar class="footbar" toggleable="sm" type="light">
    <BNavbarToggle target="nav-text-collapse" />
    <img src="/LOGO_B.png" width="120" height="120" class="d-inline-block align-top" alt="Logo">
    <BCollapse id="nav-text-collapse" is-nav>
      <BNavbarNav>
        <BNavText class="footbar">© 2026 Synapxion. Todos los derechos reservados.</BNavText>
        <BNavText class="footbar2">Developing Software for Experiences.</BNavText>
      </BNavbarNav>
    </BCollapse>
  </BNavbar>
</template>

<style scoped>
.footbar {
  background-color:  #fa4f84;
  color: #ffffff;
  font-size: 18px;
}

.footbar2 {
  margin-left: 5in;
  background-color:  #fa4f84;
  color: #ffffff;
  font-size: 18px;
}
</style>
