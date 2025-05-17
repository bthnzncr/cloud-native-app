import { defineStore } from 'pinia'
import axios from 'axios'
import api from '@/services/api'

export interface NewsItem {
  id: string
  title: string
  description: string
  publishedAt: string
  source: string
  category?: string
  imageUrl?: string
  link: string
  provider?: string
}

export const useNewsStore = defineStore('news', {
  state: () => ({
    newsItems: [] as NewsItem[], // Initialize with mock data by default
    loading: false,
    loadingMore: false, // Separate loading state for infinite scrolling
    error: null as string | null,
    currentPage: 1,
    totalItems: 0,
    hasMore: true,
    limit: 32,
    allNewsItems: [] as NewsItem[],
    currentCategory: '' as string,
    searchQuery: '' as string
  }),
  
  actions: {
    async fetchNews(reset = true) {
      this.loading = true;
      this.error = null;
      this.currentCategory = '';
      
      // Reset pagination if requested
      if (reset) {
        this.currentPage = 1;
        this.newsItems = [];
      }
      
      console.log(`Fetching news: page ${this.currentPage}, limit ${this.limit}`);
      
      try {
        // Use the new api.getAllNews method
        const result = await api.getAllNews(this.currentPage, this.limit);
        
        console.log(`API response:`, result);
        
        // New items are already mapped in api.ts
        const newItems = result.articles;
        
        // Update total and pagination info
        this.totalItems = result.total || 0;
        
        // Append items if loading more, otherwise replace
        if (reset) {
          this.newsItems = newItems;
        } else {
          this.newsItems = [...this.newsItems, ...newItems];
        }
        
        console.log(`Total items: ${this.totalItems}, Current items: ${this.newsItems.length}`);
        
        // Check if we've reached the end
        this.hasMore = this.newsItems.length < this.totalItems;
        
        console.log(`Has more: ${this.hasMore}`);
      } catch (error) {
        console.error('Error fetching news:', error);
        this.error = 'Failed to load news items';
      } finally {
        this.loading = false;
      }
    },
    
    async fetchNewsByCategory(category: string, reset = true) {
      // Use appropriate loading state based on whether this is initial load or "load more"
      if (reset) {
        this.loading = true;
      } else {
        this.loadingMore = true;
      }
      
      this.error = null;
      this.currentCategory = category;
      
      // Reset pagination if requested
      if (reset) {
        this.currentPage = 1;
        this.newsItems = [];
      }
      
      console.log(`Fetching news by category ${category}: page ${this.currentPage}, limit ${this.limit}`);
      
      try {
        const result = await api.getNewsByCategory(category, this.currentPage, this.limit);
        
        // Update total and pagination info
        this.totalItems = result.total || 0;
        
        // Append items if loading more, otherwise replace
        if (reset) {
          this.newsItems = result.articles;
        } else {
          this.newsItems = [...this.newsItems, ...result.articles];
        }
        
        console.log(`Total items: ${this.totalItems}, Current items: ${this.newsItems.length}`);
        
        // Check if we've reached the end
        this.hasMore = this.newsItems.length < this.totalItems;
        
        console.log(`Has more: ${this.hasMore}`);
      } catch (error) {
        console.error(`Error fetching ${category} news:`, error);
        this.error = `Failed to load ${category} news items`;
      } finally {
        // Clear the appropriate loading state
        if (reset) {
          this.loading = false;
        } else {
          this.loadingMore = false;
        }
      }
    },
    
    async loadMoreSilently() {
      if (!this.loading && !this.loadingMore && this.hasMore) {
        console.log('Loading more articles silently...');
        this.loadingMore = true;
        this.currentPage++;
        
        try {
          if (this.searchQuery) {
            // Load more search results
            const result = await api.searchNews(this.searchQuery, this.currentPage, this.limit);
            
            // Update total and pagination info
            this.totalItems = result.total || 0;
            
            // Append new items
            this.newsItems = [...this.newsItems, ...result.articles];
            
            // Check if we've reached the end
            this.hasMore = this.newsItems.length < this.totalItems;
          } else if (this.currentCategory) {
            const result = await api.getNewsByCategory(this.currentCategory, this.currentPage, this.limit);
            
            // Update total and pagination info
            this.totalItems = result.total || 0;
            
            // Append new items
            this.newsItems = [...this.newsItems, ...result.articles];
            
            // Check if we've reached the end
            this.hasMore = this.newsItems.length < this.totalItems;
          } else {
            // Use the new api.getAllNews method
            const result = await api.getAllNews(this.currentPage, this.limit);
            
            // New items are already mapped in api.ts
            const newItems = result.articles;
            
            // Update total and pagination info
            this.totalItems = result.total || 0;
            
            // Append new items
            this.newsItems = [...this.newsItems, ...newItems];
            
            // Check if we've reached the end
            this.hasMore = this.newsItems.length < this.totalItems;
          }
        } catch (error) {
          console.error('Error loading more articles silently:', error);
          // We don't set error state here to keep the UI clean
        } finally {
          this.loadingMore = false;
        }
      } else {
        console.log(`Not loading more: loading=${this.loading}, loadingMore=${this.loadingMore}, hasMore=${this.hasMore}`);
      }
    },
    
    async loadMore() {
      if (!this.loading && !this.loadingMore && this.hasMore) {
        console.log('Loading more articles...');
        this.currentPage++;
        
        if (this.searchQuery) {
          await this.searchNews(this.searchQuery, false);
        } else if (this.currentCategory) {
          await this.fetchNewsByCategory(this.currentCategory, false);
        } else {
          await this.fetchNews(false);
        }
      } else {
        console.log(`Not loading more: loading=${this.loading}, loadingMore=${this.loadingMore}, hasMore=${this.hasMore}`);
      }
    },
    
    async searchNews(query: string, reset = true) {
      // Use appropriate loading state based on whether this is initial load or "load more"
      if (reset) {
        this.loading = true;
      } else {
        this.loadingMore = true;
      }
      
      this.error = null;
      this.searchQuery = query;
      this.currentCategory = '';
      
      // Reset pagination if requested
      if (reset) {
        this.currentPage = 1;
        this.newsItems = [];
      }
      
      console.log(`Searching news for "${query}": page ${this.currentPage}, limit ${this.limit}`);
      
      try {
        const result = await api.searchNews(query, this.currentPage, this.limit);
        
        // Update total and pagination info
        this.totalItems = result.total || 0;
        
        // Append items if loading more, otherwise replace
        if (reset) {
          this.newsItems = result.articles;
        } else {
          this.newsItems = [...this.newsItems, ...result.articles];
        }
        
        console.log(`Total items: ${this.totalItems}, Current items: ${this.newsItems.length}`);
        
        // Check if we've reached the end
        this.hasMore = this.newsItems.length < this.totalItems;
        
        console.log(`Has more: ${this.hasMore}`);
      } catch (error) {
        console.error(`Error searching news for "${query}":`, error);
        this.error = `Failed to search for "${query}"`;

      } finally {
        // Clear the appropriate loading state
        if (reset) {
          this.loading = false;
        } else {
          this.loadingMore = false;
        }
      }
    }
  }
})