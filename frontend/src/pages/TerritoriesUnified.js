import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polygon, Marker, Popup, useMapEvents } from 'react-leaflet';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import { MapPin, Plus, Filter, Eye } from 'lucide-react';
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
  { value: 'job', label: 'Job', color: 'blue' },
  { value: 'supplier', label: 'Supplier', color: 'green' },
  { value: 'vendor', label: 'Vendor', color: 'orange' },
  { value: 'shop', label: 'Shop', color: 'red' },
  { value: 'office', label: 'Office', color: 'violet' },
  { value: 'warehouse', label: 'Warehouse', color: 'grey' },
  { value: 'service_center', label: 'Service Center', color: 'yellow' },
  { value: 'event_venue', label: 'Event Venue', color: 'red' },
  { value: 'project_site', label: 'Project Site', color: 'orange' },
  { value: 'residential_area', label: 'Residential Area', color: 'blue' },
  { value: 'parking_logistics', label: 'Parking / Logistics', color: 'grey' },
  { value: 'landmark', label: 'Landmark / Attraction', color: 'gold' },
];

// Ahmedabad Pincode Boundaries (sample data)
const PINCODE_BOUNDARIES = {
  '380001': [[23.0350, 72.5850], [23.0380, 72.5900], [23.0360, 72.5950], [23.0320, 72.5920], [23.0350, 72.5850]],
  '380004': [[23.0200, 72.5700], [23.0250, 72.5750], [23.0230, 72.5800], [23.0180, 72.5780], [23.0200, 72.5700]],
  '380006': [[23.0280, 72.5600], [23.0330, 72.5650], [23.0310, 72.5700], [23.0260, 72.5680], [23.0280, 72.5600]],
  '380009': [[23.0400, 72.5500], [23.0450, 72.5550], [23.0430, 72.5600], [23.0380, 72.5580], [23.0400, 72.5500]],
  '380015': [[23.0100, 72.5800], [23.0150, 72.5850], [23.0130, 72.5900], [23.0080, 72.5880], [23.0100, 72.5800]],
  '380052': [[23.0500, 72.5400], [23.0550, 72.5450], [23.0530, 72.5500], [23.0480, 72.5480], [23.0500, 72.5400]],
  '380054': [[23.0150, 72.4900], [23.0200, 72.4950], [23.0180, 72.5000], [23.0130, 72.4980], [23.0150, 72.4900]],
  '380061': [[23.0600, 72.5300], [23.0650, 72.5350], [23.0630, 72.5400], [23.0580, 72.5380], [23.0600, 72.5300]],
};

const LocationPicker = ({ onLocationSelect }) => {
  const [marker, setMarker] = useState(null);
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      setMarker({ lat, lng });
      onLocationSelect({ lat, lng });
    },
  });
  return marker ? <Marker position={[marker.lat, marker.lng]}><Popup><div className="text-sm"><strong>Selected</strong><br/>Lat: {marker.lat.toFixed(6)}<br/>Lng: {marker.lng.toFixed(6)}</div></Popup></Marker> : null;
};

export const TerritoriesUnified = () => {
  const [territories, setTerritories] = useState([]);
  const [pins, setPins] = useState([]);
  const [mapCenter] = useState(AHMEDABAD_CENTER);
  const [showTerritoryDialog, setShowTerritoryDialog] = useState(false);
  const [showPinDialog, setShowPinDialog] = useState(false);
  const [showFilterDialog, setShowFilterDialog] = useState(false);
  const [isPickingLocation, setIsPickingLocation] = useState(false);
  const [currentMode, setCurrentMode] = useState(null);
  const [selectedTerritoryView, setSelectedTerritoryView] = useState(null);
  const [viewOnlySelected, setViewOnlySelected] = useState(false);
  const [activeFilters, setActiveFilters] = useState([]);

  const [territoryForm, setTerritoryForm] = useState({ name: '', city: 'Ahmedabad', zone: '', pincode: '' });
  const [pinForm, setPinForm] = useState({ location: { lat: 23.0225, lng: 72.5714 }, type: [], label: '', description: '', hasGeofence: false, geofenceRadius: 1000, territoryId: '', generateAIInsights: false });

  useEffect(() => { loadData(); }, []);

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
    if (currentMode === 'pin') setPinForm({ ...pinForm, location });
  };

  const handleCreateTerritory = async (e) => {
    e.preventDefault();
    const boundary = PINCODE_BOUNDARIES[territoryForm.pincode];
    if (!boundary) {
      toast.error('Invalid pincode or boundary not available');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const lats = boundary.map(c => c[0]);
      const lngs = boundary.map(c => c[1]);
      const center = { lat: lats.reduce((a, b) => a + b) / lats.length, lng: lngs.reduce((a, b) => a + b) / lngs.length };
      
      await axios.post(`${BACKEND_URL}/api/territories`, {
        ...territoryForm,
        center,
        radius: 5000,
        boundary: boundary,
        metrics: { investments: 0, buildings: 0, populationDensity: 0, qualityOfProject: 0, govtInfra: 0, livabilityIndex: 0, airPollutionIndex: 0, roads: 0, crimeRate: 0 },
      }, { headers: { Authorization: `Bearer ${token}` } });
      toast.success(`Territory created for pincode ${territoryForm.pincode}!`);
      setShowTerritoryDialog(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create territory');
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
      setPinForm({ location: { lat: 23.0225, lng: 72.5714 }, type: [], label: '', description: '', hasGeofence: false, geofenceRadius: 1000, territoryId: '', generateAIInsights: false });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create pin');
    }
  };

  const handlePinTypeToggle = (type) => {
    setPinForm(prev => ({ ...prev, type: prev.type.includes(type) ? prev.type.filter(t => t !== type) : [...prev.type, type] }));
  };

  const toggleFilter = (type) => {
    setActiveFilters(prev => prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]);
  };

  const filteredPins = activeFilters.length > 0 ? pins.filter(pin => pin.type.some(t => activeFilters.includes(t))) : pins;
  
  const displayTerritories = viewOnlySelected && selectedTerritoryView ? territories.filter(t => t.id === selectedTerritoryView) : territories;
  
  const displayPins = viewOnlySelected && selectedTerritoryView ? filteredPins.filter(p => p.territoryId === selectedTerritoryView) : filteredPins;

  const isPinInTerritory = (pin, territory) => {
    if (!territory.boundary) return false;
    const point = [pin.location.lat, pin.location.lng];
    const polygon = territory.boundary;
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const xi = polygon[i][1], yi = polygon[i][0];
      const xj = polygon[j][1], yj = polygon[j][0];
      const intersect = ((yi > point[1]) !== (yj > point[1])) && (point[0] < (xj - xi) * (point[1] - yi) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  };

  return (
    <div className="map-management-page">
      <div className="glass-header">
        <div className="flex items-center justify-between">
          <h1 className="text-4xl font-bold text-gray-800">Ahmedabad</h1>
          <div className="flex gap-2">
            <Button onClick={() => setShowTerritoryDialog(true)} className="glass-button" data-testid="create-territory-btn">
              <Plus className="w-4 h-4 mr-2" />Create Territory
            </Button>
            <Button onClick={() => { setCurrentMode('pin'); setIsPickingLocation(true); setShowPinDialog(true); }} className="glass-button-orange">
              <MapPin className="w-4 h-4 mr-2" />Add Pin
            </Button>
            <Button onClick={() => setShowFilterDialog(true)} variant="outline" className="glass-button">
              <Filter className="w-4 h-4 mr-2" />Filter ({activeFilters.length})
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-4 mt-4">
          <div className="flex items-center gap-2">
            <Switch checked={viewOnlySelected} onCheckedChange={setViewOnlySelected} />
            <Label className="text-sm">View Selected Territory Only</Label>
          </div>
          {viewOnlySelected && (
            <Select value={selectedTerritoryView || ''} onValueChange={setSelectedTerritoryView}>
              <SelectTrigger className="w-64"><SelectValue placeholder="Select territory" /></SelectTrigger>
              <SelectContent>{territories.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
            </Select>
          )}
        </div>
      </div>

      <div className="map-container" style={{ height: 'calc(100vh - 180px)', margin: '1rem' }}>
        <MapContainer center={mapCenter} zoom={12} style={{ height: '100%', width: '100%' }}>
          <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {isPickingLocation && <LocationPicker onLocationSelect={handleLocationPicked} />}

          {displayTerritories.map((t) => (
            <Polygon key={t.id} positions={t.boundary || [[t.center.lat, t.center.lng]]} pathOptions={{ color: '#ff6b35', fillColor: '#ff6b35', fillOpacity: 0.15, weight: 3 }}>
              <Popup>
                <div className="p-3 min-w-[250px]">
                  <h3 className="font-bold text-lg text-orange-600">{t.name}</h3>
                  <p className="text-sm text-gray-600">{t.city} - {t.zone}</p>
                  <div className="mt-2 text-sm">
                    <div className="flex justify-between"><span>Appreciation:</span><span className="font-bold text-green-600">{t.aiInsights?.appreciationPercent || 0}%</span></div>
                    <div className="flex justify-between"><span>Pins Inside:</span><span className="font-bold">{pins.filter(p => isPinInTerritory(p, t)).length}</span></div>
                  </div>
                </div>
              </Popup>
            </Polygon>
          ))}

          {displayPins.map((pin) => {
            const primaryType = pin.type[0] || 'job';
            const inTerritory = displayTerritories.some(t => isPinInTerritory(pin, t));
            return (
              <React.Fragment key={pin.id}>
                <Marker position={[pin.location.lat, pin.location.lng]} icon={pinIcons[primaryType] || pinIcons.job} opacity={inTerritory ? 1 : 0.6}>
                  <Popup>
                    <div className="p-3">
                      <h4 className="font-bold">{pin.label}</h4>
                      <div className="flex flex-wrap gap-1 my-2">
                        {pin.type.map(t => <span key={t} className="text-xs px-2 py-1 bg-orange-100 text-orange-800 rounded">{PIN_TYPES.find(pt => pt.value === t)?.label || t}</span>)}
                      </div>
                      {inTerritory && <p className="text-xs text-green-600 font-semibold">✓ Inside Territory</p>}
                      {pin.hasGeofence && <p className="text-xs text-blue-600">Geofence: {pin.geofenceRadius}m</p>}
                    </div>
                  </Popup>
                </Marker>
                {pin.hasGeofence && <Circle center={[pin.location.lat, pin.location.lng]} radius={pin.geofenceRadius} pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.1, weight: 2 }} />}
              </React.Fragment>
            );
          })}
        </MapContainer>
      </div>

      <Dialog open={showTerritoryDialog} onOpenChange={setShowTerritoryDialog}>
        <DialogContent className="glass-dialog">
          <DialogHeader><DialogTitle>Create Territory by Pincode</DialogTitle><DialogDescription>Enter Ahmedabad pincode to generate boundary</DialogDescription></DialogHeader>
          <form onSubmit={handleCreateTerritory} className="space-y-4">
            <div><Label>Territory Name</Label><Input value={territoryForm.name} onChange={(e) => setTerritoryForm({ ...territoryForm, name: e.target.value })} placeholder="Vastrapur" required /></div>
            <div><Label>Zone</Label><Input value={territoryForm.zone} onChange={(e) => setTerritoryForm({ ...territoryForm, zone: e.target.value })} placeholder="West Ahmedabad" required /></div>
            <div><Label>Pincode *</Label><Input value={territoryForm.pincode} onChange={(e) => setTerritoryForm({ ...territoryForm, pincode: e.target.value })} placeholder="380001" required />
              <p className="text-xs text-gray-500 mt-1">Available: 380001, 380004, 380006, 380009, 380015, 380052, 380054, 380061</p>
            </div>
            <div className="flex gap-2"><Button type="submit" className="glass-button-orange">Create Territory</Button><Button type="button" variant="outline" onClick={() => setShowTerritoryDialog(false)}>Cancel</Button></div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showPinDialog} onOpenChange={setShowPinDialog}>
        <DialogContent className="glass-dialog max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>Create Pin</DialogTitle><DialogDescription>Click map for location</DialogDescription></DialogHeader>
          <form onSubmit={handleCreatePin} className="space-y-4">
            <div><Label>Label *</Label><Input value={pinForm.label} onChange={(e) => setPinForm({ ...pinForm, label: e.target.value })} placeholder="ABC Supplier" required /></div>
            <div><Label>Pin Types *</Label>
              <div className="grid grid-cols-3 gap-2 max-h-[180px] overflow-y-auto p-2 border rounded">
                {PIN_TYPES.map(type => <div key={type.value} className="flex items-center gap-2"><Checkbox checked={pinForm.type.includes(type.value)} onCheckedChange={() => handlePinTypeToggle(type.value)} /><label className="text-sm cursor-pointer">{type.label}</label></div>)}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Lat *</Label><Input type="number" step="any" value={pinForm.location.lat} onChange={(e) => setPinForm({ ...pinForm, location: { ...pinForm.location, lat: parseFloat(e.target.value) || 23.0225 } })} required /></div>
              <div><Label>Lng *</Label><Input type="number" step="any" value={pinForm.location.lng} onChange={(e) => setPinForm({ ...pinForm, location: { ...pinForm.location, lng: parseFloat(e.target.value) || 72.5714 } })} required /></div>
            </div>
            <div className="border-t pt-3"><div className="flex items-center justify-between mb-2"><Label>Pin Geofence</Label><Checkbox checked={pinForm.hasGeofence} onCheckedChange={(checked) => setPinForm({ ...pinForm, hasGeofence: checked })} /></div>
              {pinForm.hasGeofence && <div><Label>Radius (m)</Label><Input type="number" value={pinForm.geofenceRadius} onChange={(e) => setPinForm({ ...pinForm, geofenceRadius: parseInt(e.target.value) || 1000 })} /></div>}
            </div>
            <div><Label>Link to Territory</Label>
              <Select value={pinForm.territoryId} onValueChange={(value) => setPinForm({ ...pinForm, territoryId: value })}>
                <SelectTrigger><SelectValue placeholder="Optional" /></SelectTrigger>
                <SelectContent><SelectItem value="">None</SelectItem>{territories.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="flex gap-2"><Button type="submit" className="glass-button-orange">Create</Button><Button type="button" variant="outline" onClick={() => { setShowPinDialog(false); setIsPickingLocation(false); }}>Cancel</Button></div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showFilterDialog} onOpenChange={setShowFilterDialog}>
        <DialogContent className="glass-dialog max-w-md">
          <DialogHeader><DialogTitle>Filter Pin Types</DialogTitle><DialogDescription>Select types to show on map</DialogDescription></DialogHeader>
          <div className="space-y-3">
            <div className="flex items-center justify-between"><span className="text-sm font-medium">Selected: {activeFilters.length} / {PIN_TYPES.length}</span><Button size="sm" variant="outline" onClick={() => setActiveFilters([])}>Clear All</Button></div>
            <div className="grid grid-cols-2 gap-3 max-h-[400px] overflow-y-auto p-2">
              {PIN_TYPES.map(type => (
                <div key={type.value} className="flex items-center gap-2 p-2 border rounded hover:bg-accent">
                  <Checkbox checked={activeFilters.includes(type.value)} onCheckedChange={() => toggleFilter(type.value)} />
                  <label className="text-sm cursor-pointer flex-1">{type.label}</label>
                </div>
              ))}
            </div>
            <Button onClick={() => setShowFilterDialog(false)} className="w-full">Apply Filters</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};