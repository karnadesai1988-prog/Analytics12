import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Popup, useMapEvents } from 'react-leaflet';
import { territoryAPI } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { MapPin, Plus, Target, Search, Layers, Share2 } from 'lucide-react';
import axios from 'axios';
import L from 'leaflet';
import '../pages/MapManagement.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const AHMEDABAD_CENTER = [23.0225, 72.5714];

const pinIcons = {
  job: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  supplier: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  vendor: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  shop: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  office: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  warehouse: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  service_center: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  event_venue: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  project_site: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  residential_area: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  parking_logistics: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
  landmark: new L.Icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34] }),
};

const PIN_TYPES = [
  { value: 'job', label: 'Job' },
  { value: 'supplier', label: 'Supplier' },
  { value: 'vendor', label: 'Vendor' },
  { value: 'shop', label: 'Shop' },
  { value: 'office', label: 'Office' },
  { value: 'warehouse', label: 'Warehouse' },
  { value: 'service_center', label: 'Service Center' },
  { value: 'event_venue', label: 'Event Venue' },
  { value: 'project_site', label: 'Project Site' },
  { value: 'residential_area', label: 'Residential Area' },
  { value: 'parking_logistics', label: 'Parking / Logistics' },
  { value: 'landmark', label: 'Landmark / Attraction' },
];

const LocationPicker = ({ onLocationSelect }) => {
  const [marker, setMarker] = useState(null);
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      setMarker({ lat, lng });
      onLocationSelect({ lat, lng });
    },
  });
  return marker ? (
    <Marker position={[marker.lat, marker.lng]}>
      <Popup><div className="text-sm"><strong>Selected</strong><br/>Lat: {marker.lat.toFixed(6)}<br/>Lng: {marker.lng.toFixed(6)}</div></Popup>
    </Marker>
  ) : null;
};

export const TerritoriesUnified = () => {
  const [territories, setTerritories] = useState([]);
  const [pins, setPins] = useState([]);
  const [mapCenter] = useState(AHMEDABAD_CENTER);
  const [showTerritoryDialog, setShowTerritoryDialog] = useState(false);
  const [showPinDialog, setShowPinDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [showMetricsDialog, setShowMetricsDialog] = useState(false);
  const [isPickingLocation, setIsPickingLocation] = useState(false);
  const [currentMode, setCurrentMode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [shareLink, setShareLink] = useState('');
  const [selectedTerritory, setSelectedTerritory] = useState(null);

  const [territoryForm, setTerritoryForm] = useState({
    name: '', city: 'Ahmedabad', zone: '',
    center: { lat: 23.0225, lng: 72.5714 }, radius: 5000,
  });

  const [metricsData, setMetricsData] = useState({
    investments: 0, buildings: 0, populationDensity: 0,
    qualityOfProject: 0, govtInfra: 0, livabilityIndex: 0,
    airPollutionIndex: 0, roads: 0, crimeRate: 0
  });

  const [pinForm, setPinForm] = useState({
    location: { lat: 23.0225, lng: 72.5714 }, type: [], label: '',
    description: '', address: '', hasGeofence: false, geofenceRadius: 1000,
    territoryId: '', generateAIInsights: false,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const [territoriesRes, pinsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/territories`, { headers }),
        axios.get(`${BACKEND_URL}/api/pins`, { headers }),
      ]);
      setTerritories(territoriesRes.data);
      setPins(pinsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleLocationPicked = (location) => {
    if (currentMode === 'territory') {
      setTerritoryForm({ ...territoryForm, center: location });
    } else if (currentMode === 'pin') {
      setPinForm({ ...pinForm, location });
    }
  };

  const handleCreateTerritory = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/territories`, {
        ...territoryForm,
        metrics: { investments: 0, buildings: 0, populationDensity: 0, qualityOfProject: 0, govtInfra: 0, livabilityIndex: 0, airPollutionIndex: 0, roads: 0, crimeRate: 0 },
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Territory created with 5km geofence!');
      setShowTerritoryDialog(false);
      setIsPickingLocation(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create territory');
    }
  };

  const handleUpdateMetrics = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${BACKEND_URL}/api/territories/${selectedTerritory.id}`, { metrics: metricsData }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Metrics updated! Analytics refreshing...');
      setShowMetricsDialog(false);
      loadData();
    } catch (error) {
      toast.error('Failed to update metrics');
    }
  };

  const handleCreatePin = async (e) => {
    e.preventDefault();
    if (pinForm.type.length === 0) {
      toast.error('Select at least one pin type');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/pins`, pinForm, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Pin created!');
      setShowPinDialog(false);
      setIsPickingLocation(false);
      setPinForm({ location: { lat: 23.0225, lng: 72.5714 }, type: [], label: '', description: '', address: '', hasGeofence: false, geofenceRadius: 1000, territoryId: '', generateAIInsights: false });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create pin');
    }
  };

  const handlePinTypeToggle = (type) => {
    setPinForm(prev => ({ ...prev, type: prev.type.includes(type) ? prev.type.filter(t => t !== type) : [...prev.type, type] }));
  };

  const handleCreateShareLink = async (territory) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${BACKEND_URL}/api/share-links`, null, { params: { territory_id: territory.id }, headers: { Authorization: `Bearer ${token}` } });
      const fullUrl = `${window.location.origin}/share/${response.data.shareToken}`;
      setShareLink(fullUrl);
      setShowShareDialog(true);
    } catch (error) {
      toast.error('Failed to create share link');
    }
  };

  const openMetricsDialog = (territory) => {
    setSelectedTerritory(territory);
    setMetricsData(territory.metrics);
    setShowMetricsDialog(true);
  };

  return (
    <div className="map-management-page">
      <div className="glass-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Ahmedabad Territories & Map</h1>
            <p className="text-gray-600 mt-1">Interactive mapping • 5km Geofencing • 12 Pin Types • Live Analytics</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => { setCurrentMode('territory'); setIsPickingLocation(true); setShowTerritoryDialog(true); }} className="glass-button">
              <Target className="w-4 h-4 mr-2" />Create Territory
            </Button>
            <Button onClick={() => { setCurrentMode('pin'); setIsPickingLocation(true); setShowPinDialog(true); }} className="glass-button-orange">
              <MapPin className="w-4 h-4 mr-2" />Add Pin
            </Button>
          </div>
        </div>
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input placeholder="Search Ahmedabad locations..." className="pl-10 glass-input" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
          </div>
        </div>
      </div>

      <Tabs defaultValue="map" className="flex-1 flex flex-col px-4">
        <TabsList className="w-fit">
          <TabsTrigger value="map">Interactive Map</TabsTrigger>
          <TabsTrigger value="list">Territory List</TabsTrigger>
        </TabsList>

        <TabsContent value="map" className="flex-1">
          <div className="map-container" style={{ height: 'calc(100vh - 240px)' }}>
            <MapContainer center={mapCenter} zoom={12} style={{ height: '100%', width: '100%' }}>
              <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {isPickingLocation && <LocationPicker onLocationSelect={handleLocationPicked} />}

              {territories.map((t) => (
                <Circle key={t.id} center={[t.center.lat, t.center.lng]} radius={t.radius}
                  pathOptions={{ color: '#ff6b35', fillColor: '#ff6b35', fillOpacity: 0.15, weight: 3, dashArray: '10, 10' }}>
                  <Popup>
                    <div className="p-3 min-w-[280px]">
                      <h3 className="font-bold text-lg text-orange-600">{t.name}</h3>
                      <p className="text-sm text-gray-600">{t.city} - {t.zone}</p>
                      <div className="space-y-1 text-sm mt-2">
                        <div className="flex justify-between"><span>Geofence:</span><span className="font-semibold">{t.radius/1000}km</span></div>
                        <div className="flex justify-between"><span>Appreciation:</span><span className="font-bold text-green-600">{t.aiInsights?.appreciationPercent || 0}%</span></div>
                      </div>
                      <div className="flex gap-2 mt-3">
                        <Button size="sm" onClick={() => openMetricsDialog(t)}>Update Metrics</Button>
                        <Button size="sm" variant="outline" onClick={() => handleCreateShareLink(t)}><Share2 className="w-3 h-3 mr-1" />Share</Button>
                      </div>
                    </div>
                  </Popup>
                </Circle>
              ))}

              {pins.map((pin) => (
                <React.Fragment key={pin.id}>
                  <Marker position={[pin.location.lat, pin.location.lng]} icon={pinIcons[pin.type[0]] || pinIcons.job}>
                    <Popup>
                      <div className="p-3"><h4 className="font-bold">{pin.label}</h4>
                        <div className="flex flex-wrap gap-1 my-2">{pin.type.map(t => <span key={t} className="text-xs px-2 py-1 bg-orange-100 text-orange-800 rounded">{PIN_TYPES.find(pt => pt.value === t)?.label || t}</span>)}</div>
                        {pin.hasGeofence && <p className="text-xs text-blue-600 font-semibold">Geofence: {pin.geofenceRadius}m</p>}
                      </div>
                    </Popup>
                  </Marker>
                  {pin.hasGeofence && <Circle center={[pin.location.lat, pin.location.lng]} radius={pin.geofenceRadius} pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.1, weight: 2 }} />}
                </React.Fragment>
              ))}
            </MapContainer>

            <Card className="glass-legend">
              <CardContent className="p-4">
                <h4 className="font-semibold mb-2 flex items-center gap-2"><Layers className="w-4 h-4" />Legend</h4>
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full border-2 border-orange-500"></div><span>Territory 5km</span></div>
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full border-2 border-blue-500"></div><span>Pin Geofence</span></div>
                  <div className="flex items-center gap-2"><MapPin className="w-3 h-3 text-blue-600" /><span>Job/Residential</span></div>
                  <div className="flex items-center gap-2"><MapPin className="w-3 h-3 text-green-600" /><span>Supplier</span></div>
                  <div className="flex items-center gap-2"><MapPin className="w-3 h-3 text-orange-600" /><span>Vendor/Project</span></div>
                  <div className="flex items-center gap-2"><MapPin className="w-3 h-3 text-red-600" /><span>Shop/Event</span></div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="list" className="flex-1">
          <Card>
            <CardHeader><CardTitle>All Territories</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr className="border-b"><th className="text-left py-3 px-4 text-sm">Name</th><th className="text-left py-3 px-4 text-sm">City/Zone</th><th className="text-left py-3 px-4 text-sm">Appreciation</th><th className="text-left py-3 px-4 text-sm">Actions</th></tr></thead>
                  <tbody>
                    {territories.map(t => (
                      <tr key={t.id} className="border-b hover:bg-accent">
                        <td className="py-3 px-4 font-medium">{t.name}</td>
                        <td className="py-3 px-4 text-sm">{t.city} - {t.zone}</td>
                        <td className="py-3 px-4"><span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">{t.aiInsights?.appreciationPercent || 0}%</span></td>
                        <td className="py-3 px-4"><div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => openMetricsDialog(t)}>Update</Button>
                          <Button size="sm" variant="outline" onClick={() => handleCreateShareLink(t)}>Share</Button>
                        </div></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={showTerritoryDialog} onOpenChange={setShowTerritoryDialog}>
        <DialogContent className="glass-dialog">
          <DialogHeader><DialogTitle>Create Territory (5km Geofence)</DialogTitle><DialogDescription>Click map to select Ahmedabad location</DialogDescription></DialogHeader>
          <form onSubmit={handleCreateTerritory} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Name</Label><Input value={territoryForm.name} onChange={(e) => setTerritoryForm({ ...territoryForm, name: e.target.value })} placeholder="Vastrapur" required /></div>
              <div><Label>Zone</Label><Input value={territoryForm.zone} onChange={(e) => setTerritoryForm({ ...territoryForm, zone: e.target.value })} placeholder="West Ahmedabad" required /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Latitude</Label><Input type="number" step="any" value={territoryForm.center.lat} onChange={(e) => setTerritoryForm({ ...territoryForm, center: { ...territoryForm.center, lat: parseFloat(e.target.value) || 23.0225 } })} required /></div>
              <div><Label>Longitude</Label><Input type="number" step="any" value={territoryForm.center.lng} onChange={(e) => setTerritoryForm({ ...territoryForm, center: { ...territoryForm.center, lng: parseFloat(e.target.value) || 72.5714 } })} required /></div>
            </div>
            <div className="flex gap-2"><Button type="submit" className="glass-button-orange">Create</Button><Button type="button" variant="outline" onClick={() => { setShowTerritoryDialog(false); setIsPickingLocation(false); }}>Cancel</Button></div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showPinDialog} onOpenChange={setShowPinDialog}>
        <DialogContent className="glass-dialog max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>Create Pin (12 Types + Geofence)</DialogTitle><DialogDescription>Click map for Ahmedabad location</DialogDescription></DialogHeader>
          <form onSubmit={handleCreatePin} className="space-y-4">
            <div><Label>Label *</Label><Input value={pinForm.label} onChange={(e) => setPinForm({ ...pinForm, label: e.target.value })} placeholder="ABC Supplier" required /></div>
            <div><Label>Pin Types (Multi-select) *</Label>
              <div className="grid grid-cols-3 gap-2 max-h-[180px] overflow-y-auto p-2 border rounded">
                {PIN_TYPES.map(type => <div key={type.value} className="flex items-center gap-2"><Checkbox checked={pinForm.type.includes(type.value)} onCheckedChange={() => handlePinTypeToggle(type.value)} /><label className="text-sm cursor-pointer">{type.label}</label></div>)}
              </div>
              <p className="text-xs text-gray-500 mt-1">{pinForm.type.length} selected</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Lat *</Label><Input type="number" step="any" value={pinForm.location.lat} onChange={(e) => setPinForm({ ...pinForm, location: { ...pinForm.location, lat: parseFloat(e.target.value) || 23.0225 } })} required /></div>
              <div><Label>Lng *</Label><Input type="number" step="any" value={pinForm.location.lng} onChange={(e) => setPinForm({ ...pinForm, location: { ...pinForm.location, lng: parseFloat(e.target.value) || 72.5714 } })} required /></div>
            </div>
            <div className="border-t pt-3">
              <div className="flex items-center justify-between mb-2"><Label>Enable Pin Geofence</Label><Checkbox checked={pinForm.hasGeofence} onCheckedChange={(checked) => setPinForm({ ...pinForm, hasGeofence: checked })} /></div>
              {pinForm.hasGeofence && <div><Label>Radius (m)</Label><Input type="number" value={pinForm.geofenceRadius} onChange={(e) => setPinForm({ ...pinForm, geofenceRadius: parseInt(e.target.value) || 1000 })} /></div>}
            </div>
            <div className="border-t pt-3"><div className="flex items-center justify-between"><Label>AI Insights</Label><Checkbox checked={pinForm.generateAIInsights} onCheckedChange={(checked) => setPinForm({ ...pinForm, generateAIInsights: checked })} /></div></div>
            <div className="flex gap-2"><Button type="submit" className="glass-button-orange">Create</Button><Button type="button" variant="outline" onClick={() => { setShowPinDialog(false); setIsPickingLocation(false); }}>Cancel</Button></div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showMetricsDialog} onOpenChange={setShowMetricsDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>Update Metrics</DialogTitle><DialogDescription>{selectedTerritory?.name}</DialogDescription></DialogHeader>
          <form onSubmit={handleUpdateMetrics} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Investments (₹)</Label><Input type="number" value={metricsData.investments} onChange={(e) => setMetricsData({ ...metricsData, investments: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Buildings</Label><Input type="number" value={metricsData.buildings} onChange={(e) => setMetricsData({ ...metricsData, buildings: parseInt(e.target.value) || 0 })} /></div>
              <div><Label>Population</Label><Input type="number" value={metricsData.populationDensity} onChange={(e) => setMetricsData({ ...metricsData, populationDensity: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Quality (0-10)</Label><Input type="number" min="0" max="10" step="0.1" value={metricsData.qualityOfProject} onChange={(e) => setMetricsData({ ...metricsData, qualityOfProject: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Infrastructure (0-10)</Label><Input type="number" min="0" max="10" step="0.1" value={metricsData.govtInfra} onChange={(e) => setMetricsData({ ...metricsData, govtInfra: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Livability (0-10)</Label><Input type="number" min="0" max="10" step="0.1" value={metricsData.livabilityIndex} onChange={(e) => setMetricsData({ ...metricsData, livabilityIndex: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Pollution (0-10)</Label><Input type="number" min="0" max="10" step="0.1" value={metricsData.airPollutionIndex} onChange={(e) => setMetricsData({ ...metricsData, airPollutionIndex: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Roads (0-10)</Label><Input type="number" min="0" max="10" step="0.1" value={metricsData.roads} onChange={(e) => setMetricsData({ ...metricsData, roads: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Crime (0-10)</Label><Input type="number" min="0" max="10" step="0.1" value={metricsData.crimeRate} onChange={(e) => setMetricsData({ ...metricsData, crimeRate: parseFloat(e.target.value) || 0 })} /></div>
            </div>
            <div className="flex gap-2"><Button type="submit">Update</Button><Button type="button" variant="outline" onClick={() => setShowMetricsDialog(false)}>Cancel</Button></div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Share Territory Link</DialogTitle><DialogDescription>WiFi network data gathering link</DialogDescription></DialogHeader>
          <div className="space-y-3">
            <div><Label>Share URL</Label><div className="flex gap-2"><Input value={shareLink} readOnly /><Button onClick={() => { navigator.clipboard.writeText(shareLink); toast.success('Copied!'); }}>Copy</Button></div></div>
            <p className="text-sm text-muted-foreground">Share on WiFi for live submissions. Analytics update in real-time.</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};