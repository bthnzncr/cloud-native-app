import axios from 'axios'
import type { NewsItem } from '@/stores/newsStore'

// Create an Axios instance with default config
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:30000',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
})

export default {
  async getNews(): Promise<NewsItem[]> {
    const response = await apiClient.get('/api/articles?page=1&limit=20');
    
    // Map the API response to our NewsItem format
    return response.data.articles.map((article: any) => ({
      id: article._id,
      title: article.title,
      description: article.description,
      publishedAt: article.published_date,
      source: article.source,
      category: article.category,
      imageUrl: article.picture,
      link: article.link || '',
      provider: article.provider || article.source
    }));
  },
  
  async getNewsBySource(source: string): Promise<NewsItem[]> {
    const response = await apiClient.get(`/api/articles?source=${source}&page=1&limit=20`);
    
    // Map the API response to our NewsItem format
    return response.data.articles.map((article: any) => ({
      id: article._id,
      title: article.title,
      description: article.description,
      publishedAt: article.published_date,
      source: article.source,
      category: article.category,
      imageUrl: article.picture,
      link: article.link || '',
      provider: article.provider || article.source
    }));
  },
  
  async getNewsByCategory(category: string, page: number = 1, limit: number = 20): Promise<{articles: NewsItem[], total: number}> {
    const response = await apiClient.get(`/api/articles?category=${category}&page=${page}&limit=${limit}`);
    
    // Map the API response to our NewsItem format
    const articles = response.data.articles.map((article: any) => ({
      id: article._id,
      title: article.title,
      description: article.description,
      publishedAt: article.published_date,
      source: article.source,
      category: article.category,
      imageUrl: article.picture,
      link: article.link || '',
      provider: article.provider || article.source
    }));
    
    return {
      articles,
      total: response.data.total
    };
  },
  
  async searchNews(query: string, page: number = 1, limit: number = 20): Promise<{articles: NewsItem[], total: number}> {
    const response = await apiClient.get(`/api/articles?query=${encodeURIComponent(query)}&page=${page}&limit=${limit}`);
    
    // Map the API response to our NewsItem format
    const articles = response.data.articles.map((article: any) => ({
      id: article._id,
      title: article.title,
      description: article.description,
      publishedAt: article.published_date,
      source: article.source,
      category: article.category,
      imageUrl: article.picture,
      link: article.link || '',
      provider: article.provider || article.source
    }));
    
    return {
      articles,
      total: response.data.total
    };
  }
} 