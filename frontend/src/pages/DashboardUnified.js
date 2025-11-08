import React, { useEffect, useState } from 'react';
import { territoryAPI, metricsAPI } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';
import { MapPin, TrendingUp, Building, Users, Activity, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import { formatNumber, formatCurrency } from '../lib/utils';
import { Button } from '../components/ui/button';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const DashboardUnified = () => {
  const [territories, setTerritories] = useState([]);
  const [selectedTerritory, setSelectedTerritory] = useState('');
  const [history, setHistory] = useState([]);
  const [liveAnalytics, setLiveAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ totalTerritories: 0, avgAppreciation: 0, totalInvestments: 0, totalBuildings: 0 });

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    if (selectedTerritory) {
      loadAnalytics();
    }
  }, [selectedTerritory]);

  const loadDashboardData = async () => {
    try {
      const response = await territoryAPI.getAll();
      const data = response.data;
      setTerritories(data);
      if (data.length > 0) setSelectedTerritory(data[0].id);

      const totalTerritories = data.length;
      const avgAppreciation = data.reduce((sum, t) => sum + (t.aiInsights?.appreciationPercent || 0), 0) / totalTerritories || 0;
      const totalInvestments = data.reduce((sum, t) => sum + (t.metrics?.investments || 0), 0);
      const totalBuildings = data.reduce((sum, t) => sum + (t.metrics?.buildings || 0), 0);
      setStats({ totalTerritories, avgAppreciation: avgAppreciation.toFixed(2), totalInvestments, totalBuildings });
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const [historyRes, analyticsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/metrics-history/${selectedTerritory}`, { headers }),
        axios.get(`${BACKEND_URL}/api/analytics/${selectedTerritory}`, { headers })
      ]);
      setHistory(historyRes.data.map(e => ({ ...e, date: new Date(e.timestamp).toLocaleDateString() })));
      setLiveAnalytics(analyticsRes.data);
    } catch (error) {
      console.error('Failed to load analytics');
    }
  };

  const refreshAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/analytics/refresh/${selectedTerritory}`, {}, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Analytics refreshed!');
      loadAnalytics();
    } catch (error) {
      toast.error('Failed to refresh');
    }
  };

  const selectedTerritoryData = territories.find(t => t.id === selectedTerritory);
  const tenantData = liveAnalytics?.tenantDistribution ? Object.entries(liveAnalytics.tenantDistribution).map(([name, value]) => ({ name, value })) : [];
  const COLORS = ['#ff6b35', '#3b82f6', '#22c55e', '#f59e0b'];

  const statCards = [
    { title: 'Total Territories', value: stats.totalTerritories, icon: MapPin, color: 'text-blue-600', bgColor: 'bg-blue-100' },
    { title: 'Avg Appreciation', value: `${stats.avgAppreciation}%`, icon: TrendingUp, color: 'text-green-600', bgColor: 'bg-green-100' },
    { title: 'Total Investments', value: formatCurrency(stats.totalInvestments), icon: Users, color: 'text-orange-600', bgColor: 'bg-orange-100' },
    { title: 'Total Buildings', value: formatNumber(stats.totalBuildings), icon: Building, color: 'text-purple-600', bgColor: 'bg-purple-100' },
  ];

  if (loading) return <div className="flex items-center justify-center h-full"><div className="text-lg">Loading...</div></div>;

  return (
    <div className="p-6 space-y-6" data-testid="dashboard-page">
      <div className="flex items-center justify-between">
        <div><h1 className="text-3xl font-bold">Dashboard & Analytics</h1><p className="text-muted-foreground mt-1">Overview + Live Data Insights for Ahmedabad</p></div>
        {selectedTerritory && <div className="flex items-center gap-3">
          <Select value={selectedTerritory} onValueChange={setSelectedTerritory}>
            <SelectTrigger className="w-64"><SelectValue /></SelectTrigger>
            <SelectContent>{territories.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
          </Select>
          <Button onClick={refreshAnalytics} variant="outline" size="sm"><RefreshCw className="w-4 h-4" /></Button>
        </div>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, i) => (
          <motion.div key={stat.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-muted-foreground">{stat.title}</p><p className="text-2xl font-bold mt-2">{stat.value}</p></div><div className={`p-3 rounded-lg ${stat.bgColor}`}><stat.icon className={`w-6 h-6 ${stat.color}`} /></div></div></CardContent></Card>
          </motion.div>
        ))}
      </div>

      {liveAnalytics && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="w-5 h-5" />Live Data Analytics</CardTitle><CardDescription>Real-time insights from gathered data</CardDescription></CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="p-4 border rounded-lg"><h4 className="text-sm font-medium text-muted-foreground">Total Submissions</h4><p className="text-3xl font-bold mt-2">{liveAnalytics.totalSubmissions}</p><p className="text-xs text-muted-foreground mt-1">Data Quality: {liveAnalytics.dataQuality}</p></div>
              <div className="p-4 border rounded-lg"><h4 className="text-sm font-medium text-muted-foreground">Avg Property Value</h4><p className="text-2xl font-bold mt-2">{formatCurrency(liveAnalytics.avgPropertyValue)}</p></div>
              <div className="p-4 border rounded-lg"><h4 className="text-sm font-medium text-muted-foreground">Avg Rent</h4><p className="text-2xl font-bold mt-2">{formatCurrency(liveAnalytics.avgRentPrice)}</p></div>
              <div className="p-4 border rounded-lg"><h4 className="text-sm font-medium text-muted-foreground">Avg Occupancy</h4><p className="text-2xl font-bold mt-2">{liveAnalytics.avgOccupancyRate}%</p></div>
              <div className="p-4 border rounded-lg"><h4 className="text-sm font-medium text-muted-foreground">Maintenance Cost</h4><p className="text-2xl font-bold mt-2">{formatCurrency(liveAnalytics.avgMaintenanceCost)}</p></div>
              <div className="p-4 border rounded-lg"><h4 className="text-sm font-medium text-muted-foreground">Trend</h4><p className="text-2xl font-bold mt-2 text-green-600">{liveAnalytics.submissionTrend}</p></div>
            </div>
          </CardContent>
        </Card>
      )}

      {selectedTerritoryData && (
        <>
          <div className="grid md:grid-cols-3 gap-6">
            <Card><CardHeader className="pb-3"><CardTitle className="text-sm text-muted-foreground">Price Appreciation</CardTitle></CardHeader>
              <CardContent><div className="flex items-center gap-3"><div className="p-3 bg-green-100 rounded-lg"><TrendingUp className="w-6 h-6 text-green-600" /></div><div><p className="text-3xl font-bold text-green-600">{selectedTerritoryData.aiInsights?.appreciationPercent || 0}%</p><p className="text-xs text-muted-foreground">Predicted growth</p></div></div></CardContent>
            </Card>
            <Card><CardHeader className="pb-3"><CardTitle className="text-sm text-muted-foreground">Demand Pressure</CardTitle></CardHeader>
              <CardContent><div className="flex items-center gap-3"><div className="p-3 bg-blue-100 rounded-lg"><Activity className="w-6 h-6 text-blue-600" /></div><div><p className="text-3xl font-bold text-blue-600">{selectedTerritoryData.aiInsights?.demandPressure || 0}%</p><p className="text-xs text-muted-foreground">Market demand</p></div></div></CardContent>
            </Card>
            <Card><CardHeader className="pb-3"><CardTitle className="text-sm text-muted-foreground">Confidence</CardTitle></CardHeader>
              <CardContent><div><p className="text-3xl font-bold">{((selectedTerritoryData.aiInsights?.confidenceScore || 0) * 100).toFixed(0)}%</p><div className="w-full bg-secondary rounded-full h-2 mt-2"><div className="bg-primary h-2 rounded-full" style={{ width: `${(selectedTerritoryData.aiInsights?.confidenceScore || 0) * 100}%` }} /></div></div></CardContent>
            </Card>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <Card><CardHeader><CardTitle>Appreciation Trend</CardTitle></CardHeader>
              <CardContent>{history.length > 0 ? <ResponsiveContainer width="100%" height={300}><LineChart data={history}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip /><Legend /><Line type="monotone" dataKey="aiInsights.appreciationPercent" stroke="#22c55e" strokeWidth={2} name="Appreciation %" /></LineChart></ResponsiveContainer> : <div className="h-[300px] flex items-center justify-center text-muted-foreground">No data</div>}</CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Tenant Distribution</CardTitle></CardHeader>
              <CardContent>{tenantData.length > 0 ? <ResponsiveContainer width="100%" height={300}><PieChart><Pie data={tenantData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>{tenantData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer> : <div className="h-[300px] flex items-center justify-center text-muted-foreground">No tenant data</div>}</CardContent>
            </Card>
            <Card><CardHeader><CardTitle>Key Metrics</CardTitle></CardHeader>
              <CardContent><ResponsiveContainer width="100%" height={300}><BarChart data={[{ name: 'Livability', value: selectedTerritoryData.metrics?.livabilityIndex || 0 }, { name: 'Infrastructure', value: selectedTerritoryData.metrics?.govtInfra || 0 }, { name: 'Quality', value: selectedTerritoryData.metrics?.qualityOfProject || 0 }, { name: 'Roads', value: selectedTerritoryData.metrics?.roads || 0 }]}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis domain={[0, 10]} /><Tooltip /><Bar dataKey="value" fill="#ff6b35" /></BarChart></ResponsiveContainer></CardContent>
            </Card>
            <Card><CardHeader><CardTitle>AI Suggestions</CardTitle><CardDescription>Auto-generated improvements</CardDescription></CardHeader>
              <CardContent><div className="space-y-2">{(selectedTerritoryData.aiInsights?.aiSuggestions || []).length > 0 ? selectedTerritoryData.aiInsights.aiSuggestions.map((s, i) => <div key={i} className="p-3 bg-blue-50 rounded text-sm">{s}</div>) : <p className="text-muted-foreground">No suggestions available</p>}</div></CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
};