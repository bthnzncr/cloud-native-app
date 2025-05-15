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
    newsItems: generateMockNews(), // Initialize with mock data by default
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
        // Use environment variable for the API URL
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:30000';
        
        // Build the API endpoint with query parameters
        let endpoint = `/api/articles?page=${this.currentPage}&limit=${this.limit}`;
        
        // Fetch news from the API
        const response = await axios.get(`${apiUrl}${endpoint}`);
        
        console.log(`API response:`, response.data);
        
        // Map API response to our NewsItem format
        const newItems = response.data.articles.map((article: any) => ({
          id: article._id,
          title: article.title,
          description: article.description,
          publishedAt: article.published_date,
          source: article.source,
          category: article.category,
          imageUrl: article.picture,
          link: article.link,
          provider: article.provider || article.source // Use provider or fallback to source
        }));
        
        // Update total and pagination info
        this.totalItems = response.data.total || 0;
        
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
        
        if (reset) {
          // Only load mock data if this is the initial fetch
          this.newsItems = generateMockNews();
        }
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
        
        if (reset) {
          // Only load mock data if this is the initial fetch
          this.newsItems = generateMockNews().filter(item => 
            item.category?.toUpperCase() === category.toUpperCase()
          );
        }
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
            // Use environment variable for the API URL
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:30000';
            
            // Build the API endpoint with query parameters
            let endpoint = `/api/articles?page=${this.currentPage}&limit=${this.limit}`;
            
            // Fetch news from the API
            const response = await axios.get(`${apiUrl}${endpoint}`);
            
            // Map API response to our NewsItem format
            const newItems = response.data.articles.map((article: any) => ({
              id: article._id,
              title: article.title,
              description: article.description,
              publishedAt: article.published_date,
              source: article.source,
              category: article.category,
              imageUrl: article.picture,
              link: article.link,
              provider: article.provider || article.source
            }));
            
            // Update total and pagination info
            this.totalItems = response.data.total || 0;
            
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
        
        if (reset) {
          // Filter mock data for search results as a fallback
          this.newsItems = generateMockNews().filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase()) || 
            (item.description?.toLowerCase().includes(query.toLowerCase()) || false)
          );
        }
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

// Mock data for development
function generateMockNews(): NewsItem[] {
  const sources = ['BBC News', 'CNN', 'Reuters', 'The Guardian', 'Al Jazeera']
  const providers = ['BBC News', 'CNN', 'Reuters', 'The Guardian', 'Al Jazeera']
  const categories = ['TECHNOLOGY', 'BUSINESS', 'POLITICS', 'SCIENCE', 'ENTERTAINMENT', 'HEALTH', 'SPORTS', 'WORLD']
  
  // Generate mock news with random categories
  return Array.from({ length: 12 }, (_, i) => {
    const randomProvider = providers[Math.floor(Math.random() * providers.length)]
    const randomCategory = categories[Math.floor(Math.random() * categories.length)]
    
    return {
      id: `news-${i}`,
      title: `${randomCategory}: News headline ${i + 1} about current events`,
      description: `This is a sample description for news item ${i + 1}. It contains a brief overview of what the article is about.`,
      publishedAt: new Date(Date.now() - Math.floor(Math.random() * 86400000 * 5)).toISOString(),
      source: sources[Math.floor(Math.random() * sources.length)],
      imageUrl: `https://picsum.photos/500/500?random=${i}`,
      link: `https://example.com/news/${i}`,
      category: randomCategory,
      provider: randomProvider
    }
  })
} 