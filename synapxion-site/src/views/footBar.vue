<!-- FootBar -->
<template>
  <BNavbar v-b-color-mode="'light'" toggleable="sm" variant="secondary">
    <BNavbarToggle target="nav-text-collapse" />
    <BNavbarBrand>SynapXion</BNavbarBrand>
    <BCollapse id="nav-text-collapse" is-nav>
      <BNavbarNav>
        <BNavText>Developing Software for Experiences (DSFE)</BNavText>
      </BNavbarNav>
    </BCollapse>
  </BNavbar>
</template>
