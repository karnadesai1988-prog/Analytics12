import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { ClipboardList, TrendingUp, Shield, Briefcase, Heart, Wind, Utensils, Home, Users } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const DataSubmission = () => {
  const [territories, setTerritories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    territoryId: '',
    job_likelihood: 5,
    crime_rate: 5,
    security: 5,
    livelihood: 5,
    air_quality_index: 5,
    food_hygiene: 5,
    property_value: '',
    rent_average: '',
    occupancy_rate: '',
    maintenance_cost: '',
    tenant_type: 'Family',
    notes: ''
  });

  useEffect(() => {
    loadTerritories();
  }, []);

  const loadTerritories = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/territories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTerritories(response.data);
    } catch (error) {
      toast.error('Failed to load territories');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.territoryId) {
      toast.error('Please select a territory');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Prepare data
      const submissionData = {
        territoryId: formData.territoryId,
        job_likelihood: parseFloat(formData.job_likelihood),
        crime_rate: parseFloat(formData.crime_rate),
        security: parseFloat(formData.security),
        livelihood: parseFloat(formData.livelihood),
        air_quality_index: parseFloat(formData.air_quality_index),
        food_hygiene: parseFloat(formData.food_hygiene),
        property_value: formData.property_value ? parseFloat(formData.property_value) : null,
        rent_average: formData.rent_average ? parseFloat(formData.rent_average) : null,
        occupancy_rate: formData.occupancy_rate ? parseFloat(formData.occupancy_rate) : null,
        maintenance_cost: formData.maintenance_cost ? parseFloat(formData.maintenance_cost) : null,
        tenant_type: formData.tenant_type || null,
        notes: formData.notes || null
      };

      await axios.post(`${BACKEND_URL}/api/metrics`, submissionData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Metrics submitted successfully!');
      
      // Reset form
      setFormData({
        territoryId: '',
        job_likelihood: 5,
        crime_rate: 5,
        security: 5,
        livelihood: 5,
        air_quality_index: 5,
        food_hygiene: 5,
        property_value: '',
        rent_average: '',
        occupancy_rate: '',
        maintenance_cost: '',
        tenant_type: 'Family',
        notes: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit metrics');
    } finally {
      setLoading(false);
    }
  };

  const metrics = [
    { name: 'job_likelihood', label: 'Job Likelihood', icon: Briefcase, color: 'text-blue-600', description: 'Employment opportunities and job market strength' },
    { name: 'crime_rate', label: 'Crime Rate', icon: Shield, color: 'text-red-600', description: 'Safety concerns (higher = more crime)' },
    { name: 'security', label: 'Security', icon: Shield, color: 'text-green-600', description: 'Overall security and safety feeling' },
    { name: 'livelihood', label: 'Livelihood', icon: Heart, color: 'text-purple-600', description: 'Living standards and income levels' },
    { name: 'air_quality_index', label: 'Air Quality Index', icon: Wind, color: 'text-cyan-600', description: 'Air quality and pollution levels' },
    { name: 'food_hygiene', label: 'Food Hygiene', icon: Utensils, color: 'text-orange-600', description: 'Food safety and hygiene standards' }
  ];

  return (
    <div className="min-h-screen p-6" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
            <ClipboardList className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{color: '#1A1A1A'}}>Data Submission</h1>
            <p className="text-sm" style={{color: '#4F4F4F'}}>Submit territory metrics and analytics data</p>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="max-w-6xl mx-auto">
        <form onSubmit={handleSubmit}>
          <Card className="glass-panel-light border shadow-lg" style={{borderColor: '#E0E0E0'}}>
            <CardHeader>
              <CardTitle style={{color: '#1A1A1A'}}>Territory Metrics Form</CardTitle>
              <CardDescription style={{color: '#4F4F4F'}}>
                Rate each metric on a scale of 0-10 (0 = Worst, 10 = Best)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Territory Selection */}
              <div>
                <Label className="text-base font-semibold mb-2" style={{color: '#1A1A1A'}}>Select Territory *</Label>
                <select
                  value={formData.territoryId}
                  onChange={(e) => setFormData({...formData, territoryId: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border-2 transition-all"
                  style={{
                    background: 'rgba(255, 255, 255, 0.9)',
                    borderColor: '#E0E0E0',
                    color: '#1A1A1A',
                    fontSize: '14px'
                  }}
                  required
                >
                  <option value="">Choose a territory...</option>
                  {territories.map(territory => (
                    <option key={territory.id} value={territory.id} style={{background: '#FFFFFF', color: '#1A1A1A'}}>
                      {territory.name} ({territory.zone}) - {territory.pincode}
                    </option>
                  ))}
                </select>
              </div>

              {/* Core Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {metrics.map(metric => (
                  <div key={metric.name} className="glass-panel p-4 rounded-xl border" style={{borderColor: '#E0E0E0'}}>
                    <div className="flex items-center gap-3 mb-3">
                      <metric.icon className={`w-5 h-5 ${metric.color}`} />
                      <div className="flex-1">
                        <Label className="font-semibold" style={{color: '#1A1A1A'}}>{metric.label}</Label>
                        <p className="text-xs mt-0.5" style={{color: '#8C8C8C'}}>{metric.description}</p>
                      </div>
                      <span className="text-2xl font-bold bg-gradient-to-br from-blue-500 to-blue-600 bg-clip-text text-transparent">
                        {formData[metric.name]}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="10"
                      step="0.5"
                      value={formData[metric.name]}
                      onChange={(e) => setFormData({...formData, [metric.name]: e.target.value})}
                      className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                      style={{
                        background: `linear-gradient(to right, #2563EB 0%, #2563EB ${formData[metric.name] * 10}%, #E0E0E0 ${formData[metric.name] * 10}%, #E0E0E0 100%)`
                      }}
                    />
                    <div className="flex justify-between text-xs mt-1" style={{color: '#8C8C8C'}}>
                      <span>0 - Poor</span>
                      <span>10 - Excellent</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Property Information */}
              <div className="glass-panel p-5 rounded-xl border mt-6" style={{borderColor: '#E0E0E0'}}>
                <div className="flex items-center gap-2 mb-4">
                  <Home className="w-5 h-5 text-orange-500" />
                  <h3 className="font-semibold text-lg" style={{color: '#1A1A1A'}}>Property Information (Optional)</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label style={{color: '#4F4F4F'}}>Property Value (₹ Lakhs)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="e.g., 50.00"
                      value={formData.property_value}
                      onChange={(e) => setFormData({...formData, property_value: e.target.value})}
                      className="input-glass"
                    />
                  </div>
                  <div>
                    <Label style={{color: '#4F4F4F'}}>Average Rent (₹/month)</Label>
                    <Input
                      type="number"
                      placeholder="e.g., 15000"
                      value={formData.rent_average}
                      onChange={(e) => setFormData({...formData, rent_average: e.target.value})}
                      className="input-glass"
                    />
                  </div>
                  <div>
                    <Label style={{color: '#4F4F4F'}}>Occupancy Rate (%)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      max="100"
                      placeholder="e.g., 85"
                      value={formData.occupancy_rate}
                      onChange={(e) => setFormData({...formData, occupancy_rate: e.target.value})}
                      className="input-glass"
                    />
                  </div>
                  <div>
                    <Label style={{color: '#4F4F4F'}}>Maintenance Cost (₹/month)</Label>
                    <Input
                      type="number"
                      placeholder="e.g., 2000"
                      value={formData.maintenance_cost}
                      onChange={(e) => setFormData({...formData, maintenance_cost: e.target.value})}
                      className="input-glass"
                    />
                  </div>
                </div>
              </div>

              {/* Tenant Type */}
              <div>
                <Label className="flex items-center gap-2 mb-2" style={{color: '#1A1A1A'}}>
                  <Users className="w-4 h-4 text-orange-500" />
                  Tenant Type
                </Label>
                <select
                  value={formData.tenant_type}
                  onChange={(e) => setFormData({...formData, tenant_type: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border-2"
                  style={{
                    background: 'rgba(255, 255, 255, 0.9)',
                    borderColor: '#E0E0E0',
                    color: '#1A1A1A'
                  }}
                >
                  <option value="Family">Family</option>
                  <option value="Students">Students</option>
                  <option value="Working Professionals">Working Professionals</option>
                  <option value="Senior Citizens">Senior Citizens</option>
                  <option value="Mixed">Mixed</option>
                </select>
              </div>

              {/* Notes */}
              <div>
                <Label style={{color: '#1A1A1A'}}>Additional Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  placeholder="Any additional observations or comments..."
                  rows={4}
                  className="input-glass"
                />
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full btn-orange-gradient py-6 text-lg font-semibold rounded-xl"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Submitting...</span>
                  </div>
                ) : (
                  <>
                    <TrendingUp className="w-5 h-5 mr-2" />
                    Submit Metrics Data
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </form>
      </div>
    </div>
  );
};
