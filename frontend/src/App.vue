<template>
  <div class="min-h-screen bg-black text-gray-200">
    <TheNavbar />
    <main class="ml-64 pt-4 pb-8 px-4">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import TheNavbar from '@/components/TheNavbar.vue'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Ensure we start at the Home page by default
onMounted(() => {
  if (router.currentRoute.value.path !== '/' && window.location.pathname === '/') {
    router.push('/')
  }
})
</script>

<style>
body {
  background-color: black;
  color: #e2e8f0;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

/* Better typography */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-weight: 600;
}
</style> 