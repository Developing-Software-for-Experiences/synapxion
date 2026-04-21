<template>
  <BNavbar class="navbar" toggleable="lg" type="dark">
    <img src="/I__B.png" width="8%" class="d-inline-block align-top" alt="Logo">
    <BNavbarBrand href="#navbar-overview">SynapXion</BNavbarBrand>
    <BNavbarToggle target="nav-collapse" />
    <BCollapse id="nav-collapse" is-nav>
      <BNavbarNav class="navitems">
        <BNavItem href="#navbar-download">Descargar</BNavItem>
        <BNavItem href="#navbar-docs">Docs</BNavItem>
        <BNavItem href="#navbar-blogs">Blogs</BNavItem>
      </BNavbarNav>

      <BNavbarNav class="ms-auto mb-2 mb-lg-0">
        <BNavItemDropdown right>
          <template #button-content>
            <IBiTranslate font-size="24" />
          </template>
          <BDropdownItem>ES</BDropdownItem>
          <BDropdownItem>EN</BDropdownItem>
        </BNavItemDropdown>
        <BNavItemDropdown right>

          <template #button-content>
            <BAvatar size="md" />
          </template>
          <BDropdownItem>Cuenta</BDropdownItem>
          <BDropdownItem>Cerrar sesión</BDropdownItem>
        </BNavItemDropdown>
      </BNavbarNav>
      <BNavForm class="d-flex">
        <BFormInput class="me-2" placeholder="Buscar" />
        <BButton type="submit" variant="outline-success">Buscar</BButton>
      </BNavForm>
    </BCollapse>
  </BNavbar>
</template>

<style scoped>
.navbar {
  background-color: #fa4f84;
  font-size: 18px;
}

.navbar .navbar-brand,
.navbar .nav-link {
  color: #ffffff !important;
}

.navbar .dropdown-item {
  color: #ffffff !important;
}

.navbar .form-control {
  color: #ffffff;
  background-color: transparent;
  border: 1px solid #ffffff;
}

.navbar .btn {
  color: #ffffff;
  border-color: #ffffff;
}
</style>
