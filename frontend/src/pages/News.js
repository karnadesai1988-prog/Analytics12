import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Newspaper, RefreshCw, TrendingUp, AlertCircle, Briefcase, Home, Activity, Tag } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const News = () => {
  const [newsData, setNewsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadNews();
  }, []);

  const loadNews = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/news/scraped?pages=3`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewsData(response.data);
    } catch (error) {
      toast.error('Failed to load news data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadNews();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{color: '#4F4F4F'}}>Loading news...</p>
        </div>
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 7) return 'from-green-500 to-green-600';
    if (score >= 4) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
  };

  const scores = [
    { label: 'Crime Rate Score', value: newsData?.crime_rate_score, icon: AlertCircle, description: 'Safety indicator (higher = safer)' },
    { label: 'Investment Activity', value: newsData?.investment_activity_score, icon: TrendingUp, description: 'Economic growth signals' },
    { label: 'Job Market', value: newsData?.job_market_score, icon: Briefcase, description: 'Employment opportunities' },
    { label: 'Property Market', value: newsData?.property_market_score, icon: Home, description: 'Real estate activity' },
    { label: 'Infrastructure', value: newsData?.infrastructure_score, icon: Activity, description: 'Development activity' },
    { label: 'Livability Index', value: newsData?.livability_index, icon: TrendingUp, description: 'Overall quality of life' }
  ];

  return (
    <div className="min-h-screen p-6" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 shadow-lg">
            <Newspaper className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{color: '#1A1A1A'}}>News & External Data</h1>
            <p className="text-sm mt-1" style={{color: '#4F4F4F'}}>
              Live news analysis from Gujarat Samachar ({newsData?.articles_analyzed || 0} articles analyzed)
            </p>
          </div>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn-glass"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Scores Grid */}
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-4" style={{color: '#1A1A1A'}}>Calculated Metrics (0-10 Scale)</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {scores.map((score, index) => (
            <Card key={index} className="glass-panel-light border hover-lift" style={{borderColor: '#E0E0E0'}}>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${getScoreColor(score.value)} shadow-md`}>
                    <score.icon className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-3xl font-bold" style={{color: '#1A1A1A'}}>
                    {score.value || 0}<span className="text-lg text-gray-400">/10</span>
                  </span>
                </div>
                <p className="font-semibold mb-1" style={{color: '#1A1A1A'}}>{score.label}</p>
                <p className="text-xs" style={{color: '#8C8C8C'}}>{score.description}</p>
                <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full bg-gradient-to-r ${getScoreColor(score.value)} transition-all duration-500`}
                    style={{width: `${((score.value || 0) / 10) * 100}%`}}
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Statistics */}
      <Card className="glass-panel-light border mb-6" style={{borderColor: '#E0E0E0'}}>
        <CardHeader>
          <CardTitle style={{color: '#1A1A1A'}}>Analysis Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold bg-gradient-to-r from-red-500 to-red-600 bg-clip-text text-transparent">
                {newsData?.crime_mentions || 0}
              </p>
              <p className="text-sm" style={{color: '#8C8C8C'}}>Crime Mentions</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold bg-gradient-to-r from-green-500 to-green-600 bg-clip-text text-transparent">
                {newsData?.investment_mentions || 0}
              </p>
              <p className="text-sm" style={{color: '#8C8C8C'}}>Investment Mentions</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-blue-600 bg-clip-text text-transparent">
                {newsData?.job_mentions || 0}
              </p>
              <p className="text-sm" style={{color: '#8C8C8C'}}>Job Mentions</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent">
                {newsData?.property_mentions || 0}
              </p>
              <p className="text-sm" style={{color: '#8C8C8C'}}>Property Mentions</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold bg-gradient-to-r from-purple-500 to-purple-600 bg-clip-text text-transparent">
                {newsData?.infrastructure_mentions || 0}
              </p>
              <p className="text-sm" style={{color: '#8C8C8C'}}>Infrastructure Mentions</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Articles List */}
      <div>
        <h3 className="text-xl font-bold mb-4" style={{color: '#1A1A1A'}}>Recent Articles</h3>
        <div className="space-y-3">
          {newsData?.articles?.map((article, index) => (
            <Card key={index} className="glass-panel-light border hover-lift" style={{borderColor: '#E0E0E0'}}>
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center text-white font-bold text-sm">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold mb-2" style={{color: '#1A1A1A'}}>{article.title}</h4>
                    {article.tags && article.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {article.tags.map((tag, i) => (
                          <Badge key={i} className="badge-glass text-xs" style={{borderColor: '#E0E0E0'}}>
                            <Tag className="w-3 h-3 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )) || (
            <p className="text-center py-8" style={{color: '#8C8C8C'}}>No articles available</p>
          )}
        </div>
      </div>
    </div>
  );
};
