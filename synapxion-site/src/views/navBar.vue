<template>
  <BNavbar v-b-color-mode="'dark'" toggleable="lg" variant="secondary">
    <BNavbarBrand href="#navbar-overview">SynapXion</BNavbarBrand>
    <BNavbarToggle target="nav-collapse" />
    <BCollapse id="nav-collapse" is-nav>
      <BNavbarNav>
        <BNavItem href="#navbar-overview">Descargar</BNavItem>
        <BNavItem href="#navbar-overview">Docs</BNavItem>
        <BNavItem href="#navbar-overview">Blogs</BNavItem>
      </BNavbarNav>
      <!-- Right aligned nav items -->
      <BNavbarNav class="ms-auto mb-2 mb-lg-0">
        <BNavItemDropdown right>
          <template #button-content>
            <IBiTranslate font-size="24" />
          </template>
          <BDropdownItem>ES</BDropdownItem>
          <BDropdownItem>EN</BDropdownItem>
          <BDropdownItem>RU</BDropdownItem>
          <BDropdownItem>FA</BDropdownItem>
        </BNavItemDropdown>
        <BNavItemDropdown right>
          <!-- Using 'button-content' slot -->
          <template #button-content>
            <BAvatar size="md" />
          </template>
          <BDropdownItem>Cuenta</BDropdownItem>
          <BDropdownItem>Cerrar sesión</BDropdownItem>
        </BNavItemDropdown>
      </BNavbarNav>
      <BNavForm class="d-flex">
        <BFormInput class="me-2" placeholder="Search" />
        <BButton type="submit" variant="outline-success">Buscar</BButton>
      </BNavForm>
    </BCollapse>
  </BNavbar>
</template>
