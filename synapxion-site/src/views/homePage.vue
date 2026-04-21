<template>
  <div class="titlecard container-sm">
    <img class="rounded mx-auto d-block" width="70%" src="/SynapXion.png" alt="Synapxion">
    <h5 class="card-subtitle mb-2 text-muted text-center">¡Nuestro asistente Syna esta listo para servirte!</h5>
  </div>

  <div class="c"> </div>

  <div class="content-about">
    <p class="text">¡Nuestro asistente Syna esta listo para servirte!</p>
  </div>

  <div class="content-download">
    <h2 class="title">Descargas</h2>

    <div class="card-deck">
      <div class="card text-center">
      <div class="card-body">
        <h5 class="card-title">Windows</h5>
        <p class="card-text">This card has supporting text below as a natural lead-in to additional content.</p>
        <a href="#" class="btn btn-primary">Descargar</a>
      </div>
      </div>

      <div class="card text-center">
      <div class="card-body">
        <h5 class="card-title">MacOS</h5>
        <p class="card-text">This card has supporting text below as a natural lead-in to additional content.</p>
        <a href="#" class="btn btn-primary">Descargar</a>
      </div>
      </div>

      <div class="card text-center">
      <div class="card-body">
        <h5 class="card-title">Linux</h5>
        <p class="card-text">This card has supporting text below as a natural lead-in to additional content.</p>
        <a href="#" class="btn btn-primary">Descargar</a>
      </div>
      </div>
    </div>
  </div>

<div class="a"> </div>
</template>

<style scoped>
.navbar {
  background-color:  #fa4f84;
}

.titlecard {
  margin-top: 30px;
  margin-bottom: 60px;
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
  height: 948px;
  padding-left: 30px;
  padding-right: 30px;
  background-color: #449fe6;
}

.card-body{
  padding: 30px;
  padding-left: 40px;
  padding-right: 40px;
}

.c {
  padding: 6px;
  background-color: #449fe6;
}

.a {
  padding: 5px;
  background-color: #f9ae2f;
}

.title {
  margin-bottom: 25px;
  border-color: #ffffff;
}

.titlecard img {
  max-width: 100%;
  height: auto;
  display: block;
}

.content-download {
  background-image: url('Syna_.png');
  position: relative;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.content-download::before {
  content: "";
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0;
}

.content-download h2,
.content-download .card-deck {
  position: relative;
  z-index: 1;
}

</style>
