<template>
  <div class="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
    <h2 class="text-2xl font-bold mb-4 text-gray-200 mt-12">Business News</h2>
    
    <!-- Loading indicator -->
    <div v-if="newsStore.loading" class="text-center py-4">
      <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
      <p class="mt-2 text-gray-400">Loading news...</p>
    </div>
    
    <!-- News grid -->
    <div class="card-grid">
      <NewsCard 
        v-for="item in newsStore.newsItems" 
        :key="item.id" 
        :news="item" 
      />
    </div>
    
    <!-- Error message -->
    <div v-if="newsStore.error" class="bg-gray-900 border-l-4 border-blue-500 p-4 my-4">
      <p class="text-blue-400">{{ newsStore.error }}</p>
    </div>
    
    <!-- No articles message -->
    <div v-if="newsStore.newsItems.length === 0 && !newsStore.loading" class="text-center text-gray-500 py-4">
      No business news articles found
    </div>
    
    <!-- End of results message -->
    <div v-if="!newsStore.loading && !newsStore.loadingMore && !newsStore.hasMore && newsStore.newsItems.length > 0" class="text-center text-gray-500 mt-8">
      You've reached the end of the results ({{ newsStore.newsItems.length }} articles)
    </div>
    
    <!-- Back to top button -->
    <button 
      v-show="showBackToTop"
      @click="scrollToTop"
      class="fixed bottom-5 right-5 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-all"
      aria-label="Back to top"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useNewsStore } from '@/stores/newsStore'
import NewsCard from '@/components/NewsCard.vue'

const newsStore = useNewsStore()
const showBackToTop = ref(false)
const scrollThrottleTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

const loadNews = async () => {
  await newsStore.fetchNewsByCategory('BUSINESS');
}

const loadMoreSilently = async () => {
  await newsStore.loadMoreSilently()
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// Check scroll position to show/hide back to top button and load more when near bottom
const handleScroll = () => {
  // Avoid processing scroll events too frequently
  if (scrollThrottleTimeout.value) return
  
  scrollThrottleTimeout.value = setTimeout(() => {
    // Show button when scrolled down 500px
    showBackToTop.value = window.scrollY > 500
    
    // Check if we're near the bottom of the page to implement infinite scrolling
    const scrollPosition = window.innerHeight + window.scrollY
    const pageHeight = document.body.offsetHeight
    const scrollThreshold = pageHeight - 500
    
    if (scrollPosition >= scrollThreshold) {
      if (!newsStore.loading && !newsStore.loadingMore && newsStore.hasMore) {
        console.log('Near bottom of page, loading more business articles silently')
        loadMoreSilently()
      }
    }
    
    scrollThrottleTimeout.value = null
  }, 200)
}

onMounted(() => {
  // Load news immediately
  loadNews()
  
  // Add scroll event listener
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  // Clear any pending timeouts
  if (scrollThrottleTimeout.value) {
    clearTimeout(scrollThrottleTimeout.value)
  }
})
</script>

<style scoped>
.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  min-height: calc(100vh - 150px);
  grid-auto-rows: 1fr;
}
</style>