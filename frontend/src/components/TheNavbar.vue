<template>
  <div class="flex flex-col">
    <!-- Search bar at the top -->
    <div class="bg-black fixed top-0 left-64 right-0 z-10 h-12 px-4 flex items-center">
      <div class="max-w-md w-full mx-auto">
        <form @submit.prevent="submitSearch" class="relative">
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="Search..." 
            class="w-full bg-gray-800 border border-gray-700 rounded-full py-2 px-4 text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-600"
          />
          <button type="submit" class="absolute right-3 top-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
    
    <!-- Left sidebar navbar with top/middle/bottom sections -->
    <nav class="bg-black shadow fixed top-0 left-0 bottom-0 z-10 w-64 flex flex-col justify-between">
      <!-- Top section -->
      <div class="p-4">
        <div class="flex-shrink-0 flex items-center mb-6">
          <router-link to="/" class="text-3xl font-bold text-white">
            <span class="text-blue-600">N</span>ewsBundle
          </router-link>
        </div>
        
        <div class="flex flex-col space-y-4">
          <router-link 
            to="/" 
            class="nav-link"
            :class="{ 'active-link': isActiveRoute('/') }"
          >
            <span class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              All News
            </span>
          </router-link>
        </div>
      </div>
      
      <!-- Middle section -->
      <div class="flex-grow p-4 overflow-y-auto">
        <h3 class="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-3">Categories</h3>
        <div class="flex flex-col space-y-4">
          <router-link 
            to="/politics" 
            class="nav-link"
            :class="{ 'active-link': isActiveRoute('/politics') }"
          >
            Politics
          </router-link>
          
          <router-link 
            to="/business" 
            class="nav-link"
            :class="{ 'active-link': isActiveRoute('/business') }"
          >
            Business
          </router-link>
          
          <router-link 
            to="/entertainment" 
            class="nav-link"
            :class="{ 'active-link': isActiveRoute('/entertainment') }"
          >
            Entertainment
          </router-link>
        </div>
      </div>
    
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

// State
const router = useRouter()
const route = useRoute()
const searchQuery = ref('')

// Check if a route is active
const isActiveRoute = (path: string) => {
  return route.path === path
}

// Handle search form submission
const submitSearch = () => {
  // Trim and validate search query
  const query = searchQuery.value.trim()
  if (query.length > 0) {
    // Navigate to search page with query parameter
    router.push({ 
      path: '/search', 
      query: { q: query } 
    })
  }
}

// Ensure we start at the All News tab by default
onMounted(() => {
  if (window.location.pathname === '/') {
    // We're already on the home page
    console.log('Starting at All News tab')
  }
  
  // If we're on the search page, load current query into search box
  if (route.path === '/search' && route.query.q) {
    searchQuery.value = route.query.q as string
  }
})
</script>

<style scoped>
/* Custom font styling */
nav {
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.nav-link {
  display: block;
  padding: 1rem 1.25rem;
  margin-bottom: 0.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  font-size: 1.15rem;
  color: #9ca3af;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.nav-link:hover {
  color: #f3f4f6;
  background-color: rgba(59, 130, 246, 0.1);
  border-left-color: #3b82f6;
}

.active-link {
  color: white;
  font-weight: 600;
  background-color: rgba(59, 130, 246, 0.2);
  border-left: 3px solid #3b82f6;
}

/* For smoother hover transitions */
.router-link-active {
  font-weight: 600;
  color: white;
}
</style> 