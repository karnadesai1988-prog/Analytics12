import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polygon, Popup, useMap } from 'react-leaflet';
import { territoryAPI } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Plus, TrendingUp, MapPin, Building } from 'lucide-react';
import { motion } from 'framer-motion';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default icon
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const MapUpdater = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 12);
    }
  }, [center, map]);
  return null;
};

export const Territories = () => {
  const [territories, setTerritories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showMetricsDialog, setShowMetricsDialog] = useState(false);
  const [selectedTerritory, setSelectedTerritory] = useState(null);
  const [mapCenter, setMapCenter] = useState([28.6139, 77.2090]); // Delhi default

  const [formData, setFormData] = useState({
    name: '',
    city: '',
    zone: '',
    coordinates: {
      type: 'Polygon',
      coordinates: [[
        [77.2090, 28.6139],
        [77.2190, 28.6139],
        [77.2190, 28.6239],
        [77.2090, 28.6239],
        [77.2090, 28.6139]
      ]]
    },
    metrics: {
      investments: 0,
      buildings: 0,
      populationDensity: 0,
      qualityOfProject: 0,
      govtInfra: 0,
      livabilityIndex: 0,
      airPollutionIndex: 0,
      roads: 0,
      crimeRate: 0
    },
    restrictions: {
      rentFamilyOnly: false,
      pgAllowed: true
    }
  });

  const [metricsData, setMetricsData] = useState({
    investments: 0,
    buildings: 0,
    populationDensity: 0,
    qualityOfProject: 0,
    govtInfra: 0,
    livabilityIndex: 0,
    airPollutionIndex: 0,
    roads: 0,
    crimeRate: 0
  });

  useEffect(() => {
    loadTerritories();
  }, []);

  const loadTerritories = async () => {
    try {
      const response = await territoryAPI.getAll();
      setTerritories(response.data);
    } catch (error) {
      toast.error('Failed to load territories');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTerritory = async (e) => {
    e.preventDefault();
    try {
      await territoryAPI.create(formData);
      toast.success('Territory created successfully!');
      setShowCreateDialog(false);
      loadTerritories();
      // Reset form
      setFormData({
        name: '',
        city: '',
        zone: '',
        coordinates: formData.coordinates,
        metrics: {
          investments: 0,
          buildings: 0,
          populationDensity: 0,
          qualityOfProject: 0,
          govtInfra: 0,
          livabilityIndex: 0,
          airPollutionIndex: 0,
          roads: 0,
          crimeRate: 0
        },
        restrictions: {
          rentFamilyOnly: false,
          pgAllowed: true
        }
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create territory');
    }
  };

  const handleUpdateMetrics = async (e) => {
    e.preventDefault();
    try {
      await territoryAPI.update(selectedTerritory.id, {
        metrics: metricsData
      });
      toast.success('Metrics updated successfully!');
      setShowMetricsDialog(false);
      loadTerritories();
    } catch (error) {
      toast.error('Failed to update metrics');
    }
  };

  const openMetricsDialog = (territory) => {
    setSelectedTerritory(territory);
    setMetricsData(territory.metrics);
    setShowMetricsDialog(true);
  };

  const getPolygonColor = (appreciation) => {
    if (appreciation > 15) return '#22c55e';
    if (appreciation > 10) return '#eab308';
    if (appreciation > 5) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="h-full flex flex-col" data-testid="territories-page">
      {/* Header */}
      <div className="p-6 border-b bg-card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Territory Map</h1>
            <p className="text-muted-foreground mt-1">Interactive GIS visualization of territories</p>
          </div>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button data-testid="create-territory-button">
                <Plus className="w-4 h-4 mr-2" />
                Create Territory
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Territory</DialogTitle>
                <DialogDescription>
                  Add a new territory with basic information
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateTerritory} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Territory Name</Label>
                    <Input
                      id="name"
                      data-testid="territory-name-input"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="city">City</Label>
                    <Input
                      id="city"
                      data-testid="territory-city-input"
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="zone">Zone</Label>
                  <Input
                    id="zone"
                    data-testid="territory-zone-input"
                    value={formData.zone}
                    onChange={(e) => setFormData({ ...formData, zone: e.target.value })}
                    required
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" data-testid="submit-territory-button">Create Territory</Button>
                  <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative" data-testid="territory-map">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-lg text-muted-foreground">Loading map...</div>
          </div>
        ) : (
          <MapContainer
            center={mapCenter}
            zoom={12}
            style={{ height: '100%', width: '100%' }}
            className="z-0"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapUpdater center={mapCenter} />
            
            {territories.map((territory) => {
              const coords = territory.coordinates?.coordinates?.[0] || [];
              const latLngs = coords.map(coord => [coord[1], coord[0]]);
              
              return (
                <Polygon
                  key={territory.id}
                  positions={latLngs}
                  pathOptions={{
                    color: getPolygonColor(territory.aiInsights?.appreciationPercent || 0),
                    fillColor: getPolygonColor(territory.aiInsights?.appreciationPercent || 0),
                    fillOpacity: 0.4,
                    weight: 2
                  }}
                >
                  <Popup>
                    <div className="p-2 min-w-[250px]">
                      <h3 className="font-bold text-lg mb-2">{territory.name}</h3>
                      <p className="text-sm text-muted-foreground mb-3">
                        {territory.city} - {territory.zone}
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Appreciation:</span>
                          <span className="text-sm font-bold text-green-600">
                            {territory.aiInsights?.appreciationPercent || 0}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Confidence:</span>
                          <span className="text-sm font-bold">
                            {((territory.aiInsights?.confidenceScore || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Buildings:</span>
                          <span className="text-sm font-bold">
                            {territory.metrics?.buildings || 0}
                          </span>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        className="w-full mt-3"
                        onClick={() => openMetricsDialog(territory)}
                        data-testid={`update-metrics-${territory.id}`}
                      >
                        Update Metrics
                      </Button>
                    </div>
                  </Popup>
                </Polygon>
              );
            })}
          </MapContainer>
        )}

        {/* Legend */}
        <Card className="absolute bottom-4 left-4 z-[1000]">
          <CardContent className="p-4">
            <h4 className="font-semibold mb-2 text-sm">Appreciation Scale</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#22c55e' }}></div>
                <span className="text-xs">&gt;15% High</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#eab308' }}></div>
                <span className="text-xs">10-15% Good</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f97316' }}></div>
                <span className="text-xs">5-10% Moderate</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }}></div>
                <span className="text-xs">&lt;5% Low</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metrics Update Dialog */}
      <Dialog open={showMetricsDialog} onOpenChange={setShowMetricsDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Update Territory Metrics</DialogTitle>
            <DialogDescription>
              Update metrics for {selectedTerritory?.name}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdateMetrics} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="investments">Investments (₹)</Label>
                <Input
                  id="investments"
                  type="number"
                  data-testid="metrics-investments-input"
                  value={metricsData.investments}
                  onChange={(e) => setMetricsData({ ...metricsData, investments: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="buildings">Buildings</Label>
                <Input
                  id="buildings"
                  type="number"
                  data-testid="metrics-buildings-input"
                  value={metricsData.buildings}
                  onChange={(e) => setMetricsData({ ...metricsData, buildings: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="populationDensity">Population Density</Label>
                <Input
                  id="populationDensity"
                  type="number"
                  data-testid="metrics-population-input"
                  value={metricsData.populationDensity}
                  onChange={(e) => setMetricsData({ ...metricsData, populationDensity: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="qualityOfProject">Quality of Project (0-10)</Label>
                <Input
                  id="qualityOfProject"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  data-testid="metrics-quality-input"
                  value={metricsData.qualityOfProject}
                  onChange={(e) => setMetricsData({ ...metricsData, qualityOfProject: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="govtInfra">Govt Infrastructure (0-10)</Label>
                <Input
                  id="govtInfra"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={metricsData.govtInfra}
                  onChange={(e) => setMetricsData({ ...metricsData, govtInfra: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="livabilityIndex">Livability Index (0-10)</Label>
                <Input
                  id="livabilityIndex"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={metricsData.livabilityIndex}
                  onChange={(e) => setMetricsData({ ...metricsData, livabilityIndex: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="airPollutionIndex">Air Pollution Index (0-10)</Label>
                <Input
                  id="airPollutionIndex"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={metricsData.airPollutionIndex}
                  onChange={(e) => setMetricsData({ ...metricsData, airPollutionIndex: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="roads">Roads Quality (0-10)</Label>
                <Input
                  id="roads"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={metricsData.roads}
                  onChange={(e) => setMetricsData({ ...metricsData, roads: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="crimeRate">Crime Rate (0-10)</Label>
                <Input
                  id="crimeRate"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={metricsData.crimeRate}
                  onChange={(e) => setMetricsData({ ...metricsData, crimeRate: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" data-testid="submit-metrics-button">Update Metrics</Button>
              <Button type="button" variant="outline" onClick={() => setShowMetricsDialog(false)}>Cancel</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};