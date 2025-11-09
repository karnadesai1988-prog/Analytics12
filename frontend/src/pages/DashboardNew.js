import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { TrendingUp, Shield, Briefcase, Heart, Wind, Utensils, Home, DollarSign, Users, RefreshCw, Activity } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const DashboardNew = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [territories, setTerritories] = useState([]);
  const [selectedTerritory, setSelectedTerritory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadTerritories();
    loadDashboard();
  }, []);

  useEffect(() => {
    if (!loading) {
      loadDashboard();
    }
  }, [selectedTerritory]);

  const loadTerritories = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/territories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTerritories(response.data);
    } catch (error) {
      console.error('Failed to load territories');
    }
  };

  const loadDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const url = selectedTerritory === 'all' 
        ? `${BACKEND_URL}/api/analytics/dashboard`
        : `${BACKEND_URL}/api/analytics/dashboard?territory_id=${selectedTerritory}`;
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadDashboard();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{color: '#4F4F4F'}}>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const metrics = dashboardData?.metrics || {};
  const property = dashboardData?.property || {};
  const newsMetrics = dashboardData?.news_metrics || {};

  const metricsCards = [
    { label: 'Job Likelihood', value: metrics.job_likelihood, icon: Briefcase, color: 'from-blue-500 to-blue-600', max: 10 },
    { label: 'Crime Rate', value: metrics.crime_rate, icon: Shield, color: 'from-red-500 to-red-600', max: 10, inverse: true },
    { label: 'Security', value: metrics.security, icon: Shield, color: 'from-green-500 to-green-600', max: 10 },
    { label: 'Livelihood', value: metrics.livelihood, icon: Heart, color: 'from-purple-500 to-purple-600', max: 10 },
    { label: 'Air Quality', value: metrics.air_quality_index, icon: Wind, color: 'from-cyan-500 to-cyan-600', max: 10 },
    { label: 'Food Hygiene', value: metrics.food_hygiene, icon: Utensils, color: 'from-orange-500 to-orange-600', max: 10 }
  ];

  const newsCards = [
    { label: 'Crime Score (News)', value: newsMetrics.crime_score, icon: Shield, color: 'from-red-500 to-red-600' },
    { label: 'Investment Score', value: newsMetrics.investment_score, icon: TrendingUp, color: 'from-green-500 to-green-600' },
    { label: 'Job Market Score', value: newsMetrics.job_score, icon: Briefcase, color: 'from-blue-500 to-blue-600' },
    { label: 'Infrastructure Score', value: newsMetrics.infrastructure_score, icon: Activity, color: 'from-purple-500 to-purple-600' }
  ];

  return (
    <div className="min-h-screen p-6" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{color: '#1A1A1A'}}>Dashboard & Analytics</h1>
          <p className="text-sm mt-1" style={{color: '#4F4F4F'}}>
            {selectedTerritory === 'all' 
              ? `Real-time metrics from ${dashboardData?.totalMetricsSubmissions || 0} submissions across ${dashboardData?.totalTerritories || 0} territories`
              : `Metrics for ${territories.find(t => t.id === selectedTerritory)?.name || 'selected territory'}`
            }
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedTerritory}
            onChange={(e) => setSelectedTerritory(e.target.value)}
            className="px-4 py-2 rounded-xl border-2 transition-all"
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              borderColor: '#E0E0E0',
              color: '#1A1A1A',
              fontSize: '14px'
            }}
          >
            <option value="all">All Territories (Overview)</option>
            {territories.map(territory => (
              <option key={territory.id} value={territory.id}>
                {territory.name} - {territory.zone}
              </option>
            ))}
          </select>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-glass"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Livability Index - Hero Card */}
      <Card className="glass-panel-light border shadow-lg mb-6" style={{borderColor: '#E0E0E0'}}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium mb-1" style={{color: '#8C8C8C'}}>Overall Livability Index</p>
              <h2 className="text-6xl font-bold bg-gradient-to-r from-blue-500 to-blue-600 bg-clip-text text-transparent">
                {metrics.livability_index || 0}<span className="text-2xl">/10</span>
              </h2>
              <p className="text-sm mt-2" style={{color: '#4F4F4F'}}>Calculated from job opportunities, safety, quality of life metrics</p>
            </div>
            <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
              <TrendingUp className="w-16 h-16 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Core Metrics */}
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-4" style={{color: '#1A1A1A'}}>Core Territory Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {metricsCards.map((metric, index) => (
            <Card key={index} className="glass-panel-light border hover-lift" style={{borderColor: '#E0E0E0'}}>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${metric.color} shadow-md`}>
                    <metric.icon className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-3xl font-bold" style={{color: '#1A1A1A'}}>
                    {metric.value || 0}<span className="text-lg text-gray-400">/{metric.max}</span>
                  </span>
                </div>
                <p className="font-semibold" style={{color: '#1A1A1A'}}>{metric.label}</p>
                <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full bg-gradient-to-r ${metric.color} transition-all duration-500`}
                    style={{width: `${((metric.value || 0) / metric.max) * 100}%`}}
                  />
                </div>
                {metric.inverse && (
                  <p className="text-xs mt-1" style={{color: '#8C8C8C'}}>Lower is better</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Property Metrics */}
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-4" style={{color: '#1A1A1A'}}>Property & Real Estate</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="glass-panel-light border" style={{borderColor: '#E0E0E0'}}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-green-500 to-green-600">
                  <Home className="w-4 h-4 text-white" />
                </div>
                <p className="text-sm font-medium" style={{color: '#8C8C8C'}}>Avg Property Value</p>
              </div>
              <p className="text-2xl font-bold" style={{color: '#1A1A1A'}}>₹{property.avg_property_value || 0}L</p>
            </CardContent>
          </Card>
          <Card className="glass-panel-light border" style={{borderColor: '#E0E0E0'}}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600">
                  <DollarSign className="w-4 h-4 text-white" />
                </div>
                <p className="text-sm font-medium" style={{color: '#8C8C8C'}}>Avg Monthly Rent</p>
              </div>
              <p className="text-2xl font-bold" style={{color: '#1A1A1A'}}>₹{property.avg_rent || 0}</p>
            </CardContent>
          </Card>
          <Card className="glass-panel-light border" style={{borderColor: '#E0E0E0'}}>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600">
                  <Users className="w-4 h-4 text-white" />
                </div>
                <p className="text-sm font-medium" style={{color: '#8C8C8C'}}>Avg Occupancy</p>
              </div>
              <p className="text-2xl font-bold" style={{color: '#1A1A1A'}}>{property.avg_occupancy || 0}%</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* News-Based External Metrics */}
      <div>
        <h3 className="text-xl font-bold mb-4" style={{color: '#1A1A1A'}}>External News Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {newsCards.map((metric, index) => (
            <Card key={index} className="glass-panel-light border hover-lift" style={{borderColor: '#E0E0E0'}}>
              <CardContent className="p-5">
                <div className={`p-3 rounded-xl bg-gradient-to-br ${metric.color} shadow-md mb-3 inline-block`}>
                  <metric.icon className="w-5 h-5 text-white" />
                </div>
                <p className="text-sm font-medium mb-1" style={{color: '#8C8C8C'}}>{metric.label}</p>
                <p className="text-3xl font-bold" style={{color: '#1A1A1A'}}>
                  {metric.value || 0}<span className="text-lg text-gray-400">/10</span>
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
