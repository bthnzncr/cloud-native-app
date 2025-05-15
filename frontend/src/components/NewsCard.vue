<template>
  <a :href="news.link" target="_blank" rel="noopener noreferrer" class="news-card shadow-md hover:shadow-lg transition-shadow duration-300 rounded-lg overflow-hidden">
    <div class="image-container bg-gray-800">
      <img 
        :src="news.imageUrl || 'https://via.placeholder.com/300'" 
        :alt="news.title"
        class="card-image"
        loading="lazy"
      />
      <div class="absolute top-2 left-2 bg-blue-600 text-white text-xs py-1 px-2 rounded">
        {{ news.source }}
      </div>
    </div>
    <div class="p-4 flex flex-col card-content">
      <h3 class="font-bold text-md mb-2 line-clamp-2 text-gray-200">{{ news.title }}</h3>
      <p class="text-gray-400 text-sm line-clamp-3 flex-grow">{{ news.description }}</p>
      <div class="mt-auto pt-2 text-xs text-gray-500">
        {{ formatDate(news.publishedAt) }}
      </div>
    </div>
  </a>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import type { NewsItem } from '@/stores/newsStore'

const props = defineProps<{
  news: NewsItem
}>()

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}
</script>

<style scoped>
.news-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background-color: #1a1a1a;
  text-decoration: none;
  color: inherit;
  border: 1px solid #333;
}

.image-container {
  position: relative;
  width: 100%;
  height: 160px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  transition: transform 0.3s ease;
}

.news-card:hover .card-image {
  transform: scale(1.05);
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 