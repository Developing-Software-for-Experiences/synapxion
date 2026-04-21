<template>
  <div class="titlecard container-sm">
    <img class="rounded mx-auto d-block" width="70%" src="/SynapXion.png" alt="Synapxion">
    <h5 class="card-subtitle mb-2 text-muted text-center">¡Nuestro asistente Syna esta listo para servirte!</h5>
  </div>

  <div class="content-about">
    <p class="text">¡Nuestro asistente Syna esta listo para servirte!</p>
  </div>

  <div class="content-download">
    <h2 class="title">Descargas</h2>

    <div class="card-deck">
      <div class="card">
      <div class="card-body">
        <h5 class="card-title">Card title</h5>
        <p class="card-text">This is a wider card with supporting text below as a natural lead-in to additional content. This content is a little bit longer.</p>
      </div>
      </div>
      <div class="card">
      <div class="card-body">
        <h5 class="card-title">Card title</h5>
        <p class="card-text">This card has supporting text below as a natural lead-in to additional content.</p>
      </div>
      </div>

      <div class="card">
      <div class="card-body">
        <h5 class="card-title">Card title</h5>
        <p class="card-text">This is a wider card with supporting text below as a natural lead-in to additional content. This card has even longer content than the first to show that equal height action.</p>
      </div>
      </div>
    </div>
  </div>
<div class="c"> </div>
</template>

<style scoped>
.navbar {
  background-color:  #fa4f84;
}

.titlecard {
  margin-top: 30px;
  margin-bottom: 55px;
  border-color: #ffffff;
}

.content-about {
  padding: 50px;
  padding-left: 30px;
  padding-right: 30px;
  background-color: #f9ae2f;
}

.content-download {
  padding-top: 25px;
  padding-bottom: 30%;
  padding-left: 30px;
  padding-right: 30px;
  background-color: #449fe6;
}

.c {
  padding: 5px;
  background-color: #f9ae2f;
}

.title {
  margin-bottom: 25px;
  border-color: #ffffff;
}

  .content-download {
  position: relative;
  background-image: url('Nube.png');
  background-size: cover;
  background-position: center;
  padding: 40px;
}

.content-download::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0;
}

.content-download h2,
.content-download .card-deck {
  position: relative;
  z-index: 1;
}

</style>
