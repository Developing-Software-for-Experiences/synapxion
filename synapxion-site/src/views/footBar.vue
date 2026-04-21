<template>
  <BNavbar class="footbar" toggleable="sm" type="light">
    <BNavbarToggle target="nav-text-collapse" />
    <img src="/LOGO_B.png" width="120" height="120" class="d-inline-block align-top" alt="Logo">
    <BCollapse id="nav-text-collapse" is-nav>
      <BNavbarNav>
        <BNavText class="footbar">Desarrollado por Developing Software for Experiences (DSFE) | 2026</BNavText>
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
</style>
