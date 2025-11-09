import React, { useEffect, useState, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Switch } from '../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { MapPin, Plus, Filter, Eye, Loader2, MessageSquare, Upload, X, Flame, User } from 'lucide-react';
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

const highlightedPinIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [35, 57],
  iconAnchor: [17, 57],
  popupAnchor: [1, -46],
  className: 'highlighted-marker'
});

// Post marker icon - using violet/pink color to distinguish from pins
const postMarkerIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34]
});

// Helper to check if a point is inside a circle (using Haversine formula)
const isPointInCircle = (point, center, radiusInMeters) => {
  const [lat1, lng1] = point;
  const lat2 = center.lat;
  const lng2 = center.lng;
  
  const R = 6371e3; // Earth radius in meters
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lng2 - lng1) * Math.PI / 180;
  
  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  
  return distance <= radiusInMeters;
};

const MapUpdater = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom || map.getZoom());
    }
  }, [center, zoom, map]);
  return null;
};

// Draggable Plus Button Component for Adding Pins/Posts
const DraggablePlusButton = ({ initialPosition, onLocationChange, onPlusClick }) => {
  const [position, setPosition] = useState(initialPosition);
  const markerRef = useRef(null);
  
  useEffect(() => {
    setPosition(initialPosition);
  }, [initialPosition]);
  
  const eventHandlers = useMemo(
    () => ({
      dragend() {
        const marker = markerRef.current;
        if (marker != null) {
          const newPos = marker.getLatLng();
          const location = { lat: newPos.lat, lng: newPos.lng };
          setPosition(location);
          onLocationChange(location);
        }
      },
      click() {
        onPlusClick();
      },
    }),
    [onLocationChange, onPlusClick],
  );

  const plusIcon = L.divIcon({
    className: 'plus-button-marker',
    html: `
      <div style="
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 237, 213, 0.95));
        backdrop-filter: blur(10px);
        border: 3px solid #f97316;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: move;
        box-shadow: 0 8px 32px rgba(249, 115, 22, 0.3);
        transition: all 0.3s ease;
      "
      onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 12px 48px rgba(249, 115, 22, 0.5)';"
      onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 8px 32px rgba(249, 115, 22, 0.3)';"
      >
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="3" stroke-linecap="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
      </div>
    `,
    iconSize: [50, 50],
    iconAnchor: [25, 25]
  });

  return (
    <Marker
      draggable={true}
      position={[position.lat, position.lng]}
      icon={plusIcon}
      eventHandlers={eventHandlers}
      ref={markerRef}
    >
      <Popup>
        <div className="text-sm">
          <strong className="text-orange-600">📍 Place Picker</strong><br/>
          <span className="text-xs text-gray-600">Drag to move • Click to create</span><br/>
          <div className="mt-2 p-2 bg-orange-50 rounded">
            <strong className="text-xs">Current Position:</strong><br/>
            <span className="text-xs font-mono">
              {position.lat.toFixed(6)}, {position.lng.toFixed(6)}
            </span>
          </div>
        </div>
      </Popup>
    </Marker>
  );
};

// Comment marker icon (purple)
const commentIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34]
});

export const TerritoriesUnified = () => {
  const navigate = useNavigate();
  const [territories, setTerritories] = useState([]);
  const [pins, setPins] = useState([]);
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState([]);
  const [mapCenter, setMapCenter] = useState(AHMEDABAD_CENTER);
  const [mapZoom, setMapZoom] = useState(12);
  
  const [showTerritoryDialog, setShowTerritoryDialog] = useState(false);
  const [showCommunityDialog, setShowCommunityDialog] = useState(false);
  const [showPinDialog, setShowPinDialog] = useState(false);
  const [showPostDialog, setShowPostDialog] = useState(false);
  const [showActionDialog, setShowActionDialog] = useState(false);
  const [showFilterDialog, setShowFilterDialog] = useState(false);
  const [showHeatMap, setShowHeatMap] = useState(false);
  
  const [selectedTerritory, setSelectedTerritory] = useState(null);
  const [viewOnlySelected, setViewOnlySelected] = useState(false);
  const [activeFilters, setActiveFilters] = useState([]);
  
  const [territoryForm, setTerritoryForm] = useState({
    name: '',
    city: 'Ahmedabad',
    pincode: ''
  });
  
  const [pinForm, setPinForm] = useState({
    location: { lat: AHMEDABAD_CENTER[0], lng: AHMEDABAD_CENTER[1] },
    type: [],
    label: '',
    description: '',
    hasGeofence: false,
    geofenceRadius: 1000,
    territoryId: '',
    generateAIInsights: false
  });

  const [postForm, setPostForm] = useState({
    text: '',
    communityId: '',
    photo: null,
    photoPreview: null
  });

  const [communityForm, setCommunityForm] = useState({
    name: '',
    description: '',
    territoryId: '',
    photo: null,
    photoPreview: null,
    canJoin: true
  });

  const [communities, setCommunities] = useState([]);

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
    
    // Check URL parameters for actions
    const params = new URLSearchParams(window.location.search);
    if (params.get('action') === 'create-community') {
      setShowCommunityDialog(true);
      // Clean URL
      window.history.replaceState({}, '', '/territories');
    }
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const [territoriesRes, pinsRes, postsRes, commentsRes, communitiesRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/territories`, { headers }),
        axios.get(`${BACKEND_URL}/api/pins`, { headers }),
        axios.get(`${BACKEND_URL}/api/posts`, { headers }),
        axios.get(`${BACKEND_URL}/api/comments`, { headers }),
        axios.get(`${BACKEND_URL}/api/communities`, { headers }),
      ]);
      setTerritories(territoriesRes.data);
      setPins(pinsRes.data);
      setPosts(postsRes.data);
      setComments(commentsRes.data);
      setCommunities(communitiesRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleLocationPicked = (location) => {
    setPinForm({ ...pinForm, location });
  };

  const handlePlusClick = () => {
    // Open action selection dialog
    setShowActionDialog(true);
  };

  const handleCreatePin = () => {
    setShowActionDialog(false);
    setShowPinDialog(true);
  };

  const handleCreatePost = () => {
    setShowActionDialog(false);
    setShowPostDialog(true);
  };

  const handleCreateTerritory = async (e) => {
    e.preventDefault();
    
    if (!territoryForm.pincode || territoryForm.pincode.length !== 6) {
      toast.error('Please enter a valid 6-digit pincode');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Create territory with pincode - backend will handle center resolution
      await axios.post(
        `${BACKEND_URL}/api/territories`,
        {
          ...territoryForm,
          radius: 2500, // 2.5km radius = 5km diameter
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
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Territory created with 5km diameter circle for pincode ${territoryForm.pincode}!`);
      setShowTerritoryDialog(false);
      setTerritoryForm({ name: '', city: 'Ahmedabad', pincode: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create territory');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitPin = async (e) => {
    e.preventDefault();
    
    if (pinForm.type.length === 0) {
      toast.error('Select at least one pin type');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/pins`, pinForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Pin created successfully!');
      setShowPinDialog(false);
      setPinForm({
        location: { lat: AHMEDABAD_CENTER[0], lng: AHMEDABAD_CENTER[1] },
        type: [],
        label: '',
        description: '',
        hasGeofence: false,
        geofenceRadius: 1000,
        territoryId: '',
        generateAIInsights: false
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create pin');
    } finally {
      setLoading(false);
    }
  };

  const handleTerritoryClick = (territory) => {
    setSelectedTerritory(territory);
    if (territory.center) {
      setMapCenter([territory.center.lat, territory.center.lng]);
      setMapZoom(13);
    }
  };

  const toggleFilter = (filterValue) => {
    setActiveFilters(prev => 
      prev.includes(filterValue)
        ? prev.filter(f => f !== filterValue)
        : [...prev, filterValue]
    );
  };

  const filteredPins = activeFilters.length > 0
    ? pins.filter(pin => pin.type.some(t => activeFilters.includes(t)))
    : pins;

  const visibleTerritories = viewOnlySelected && selectedTerritory
    ? [selectedTerritory]
    : territories;

  const visiblePins = viewOnlySelected && selectedTerritory
    ? filteredPins.filter(pin => 
        selectedTerritory.center && isPointInCircle([pin.location.lat, pin.location.lng], selectedTerritory.center, selectedTerritory.radius || 2500)
      )
    : filteredPins;

  const isPinInSelectedTerritory = (pin) => {
    if (!selectedTerritory || !selectedTerritory.center) return false;
    return isPointInCircle([pin.location.lat, pin.location.lng], selectedTerritory.center, selectedTerritory.radius || 2500);
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 sm:px-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Ahmedabad</h1>
            <p className="text-sm text-gray-500 mt-0.5">Territories & Map Management</p>
          </div>
          
          <div className="flex flex-wrap items-center gap-2">
            <Button
              onClick={() => setShowTerritoryDialog(true)}
              variant="default"
              size="sm"
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700"
            >
              <Plus className="w-4 h-4 mr-1" />
              Create Territory
            </Button>
            
            <Button
              onClick={() => setShowFilterDialog(true)}
              variant="outline"
              size="sm"
            >
              <Filter className="w-4 h-4 mr-1" />
              Filter ({activeFilters.length})
            </Button>
            
            <Button
              onClick={() => setShowHeatMap(!showHeatMap)}
              variant={showHeatMap ? "default" : "outline"}
              size="sm"
              className={showHeatMap ? "bg-gradient-to-r from-orange-500 to-orange-600" : ""}
            >
              <Eye className="w-4 h-4 mr-1" />
              {showHeatMap ? 'Show Map' : 'Heat Map'}
            </Button>
            
            <div className="text-xs text-gray-500 flex items-center gap-1 bg-orange-50 px-3 py-1 rounded-full border border-orange-200">
              <Plus className="w-3 h-3 text-orange-600" />
              <span>Drag <span className="font-semibold text-orange-600">+</span> to move, click to create</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 lg:w-80 bg-white border-r overflow-y-auto hidden md:block">
          <div className="p-4 space-y-4">
            {/* Toggle for selected territory view */}
            {selectedTerritory && (
              <Card className="p-3 bg-orange-50 border-orange-200">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Only Show Selected</Label>
                  <Switch
                    checked={viewOnlySelected}
                    onCheckedChange={setViewOnlySelected}
                  />
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {viewOnlySelected ? 'Showing only selected territory' : 'Showing all territories'}
                </p>
              </Card>
            )}

            {/* Territories List */}
            <div>
              <h3 className="font-semibold mb-2 text-sm text-gray-700">Territories ({territories.length})</h3>
              <div className="space-y-2">
                {territories.map(territory => (
                  <Card
                    key={territory.id}
                    className={`p-3 cursor-pointer transition-all hover:shadow-md ${
                      selectedTerritory?.id === territory.id ? 'border-orange-500 border-2 bg-orange-50' : ''
                    }`}
                    onClick={() => handleTerritoryClick(territory)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-semibold text-sm">{territory.name}</h4>
                        <p className="text-xs text-gray-500 mt-1">Zone: {territory.zone}</p>
                        <Badge variant="outline" className="mt-1 text-xs">
                          {territory.pincode}
                        </Badge>
                      </div>
                      {selectedTerritory?.id === territory.id && (
                        <Eye className="w-4 h-4 text-orange-500" />
                      )}
                    </div>
                    <div className="mt-2 pt-2 border-t text-xs">
                      <div className="flex justify-between mb-2">
                        <span className="text-gray-600">Appreciation:</span>
                        <span className="font-semibold text-green-600">
                          {territory.aiInsights?.appreciationPercent || 0}%
                        </span>
                      </div>
                      {selectedTerritory?.id === territory.id && (
                        <Button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/territory/${territory.id}`);
                          }}
                          size="sm"
                          variant="outline"
                          className="w-full text-xs border-orange-300 hover:bg-orange-50"
                        >
                          <User className="w-3 h-3 mr-1" />
                          View Profile
                        </Button>
                      )}
                    </div>
                  </Card>
                ))}
                {territories.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">No territories yet</p>
                )}
              </div>
            </div>

            {/* Active Filters */}
            {activeFilters.length > 0 && (
              <div>
                <h3 className="font-semibold mb-2 text-sm text-gray-700">Active Filters</h3>
                <div className="flex flex-wrap gap-1">
                  {activeFilters.map(filter => (
                    <Badge
                      key={filter}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() => toggleFilter(filter)}
                    >
                      {PIN_TYPES.find(t => t.value === filter)?.label} ×
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          <MapContainer
            center={mapCenter}
            zoom={mapZoom}
            className="w-full h-full"
            style={{ background: '#f0f0f0' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            <MapUpdater center={mapCenter} zoom={mapZoom} />
            
            {/* Draggable Plus Button for Adding Pins/Posts */}
            {!showHeatMap && (
              <DraggablePlusButton
                initialPosition={pinForm.location}
                onLocationChange={handleLocationPicked}
                onPlusClick={handlePlusClick}
              />
            )}
            
            {/* Territories as Circles */}
            {visibleTerritories.map(territory => {
              if (territory.center) {
                const radius = territory.radius || 2500; // Default 2.5km radius
                const rating = territory.rating;
                const totalScore = rating?.totalScore || 0;
                
                return (
                  <React.Fragment key={territory.id}>
                    <Circle
                      center={[territory.center.lat, territory.center.lng]}
                      radius={radius}
                      pathOptions={{
                        color: selectedTerritory?.id === territory.id ? '#f97316' : '#3b82f6',
                        weight: selectedTerritory?.id === territory.id ? 3 : 2,
                        fillOpacity: selectedTerritory?.id === territory.id ? 0.2 : 0.1
                      }}
                      eventHandlers={{
                        click: () => handleTerritoryClick(territory)
                      }}
                    >
                    <Popup maxWidth={300}>
                      <div className="text-sm space-y-2">
                        <div className="border-b pb-2">
                          <h3 className="font-bold text-base">{territory.name}</h3>
                          <p className="text-xs text-gray-600">Zone: {territory.zone} | Pincode: {territory.pincode}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <p className="text-xs text-blue-600 font-semibold">
                              🔵 5km diameter coverage
                            </p>
                            {territory.rating && territory.rating.totalScore > 0 && (
                              <div className="flex items-center gap-1 bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                                <span className="text-xs font-bold">⭐ {territory.rating.totalScore}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {territory.rating && territory.rating.totalScore > 0 && (
                          <div className="border-b pb-2">
                            <h4 className="font-semibold text-xs text-purple-600 mb-1">Rating Breakdown</h4>
                            <div className="text-xs space-y-1">
                              {territory.rating.topContributors?.slice(0, 3).map((contrib, idx) => (
                                <div key={idx} className="flex justify-between">
                                  <span>{contrib.type} ({contrib.count})</span>
                                  <span className="font-semibold">{contrib.score} pts ({contrib.percentage}%)</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        <div className="space-y-1">
                          <h4 className="font-semibold text-xs text-orange-600">AI Insights</h4>
                          <div className="grid grid-cols-2 gap-1 text-xs">
                            <span className="text-gray-600">Appreciation:</span>
                            <span className="font-semibold text-green-600">{territory.aiInsights?.appreciationPercent || 0}%</span>
                            <span className="text-gray-600">Confidence:</span>
                            <span className="font-semibold">{territory.aiInsights?.confidenceScore || 0}%</span>
                            <span className="text-gray-600">Demand:</span>
                            <span className="font-semibold">{territory.aiInsights?.demandPressure || 0}</span>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <h4 className="font-semibold text-xs text-blue-600">Key Metrics</h4>
                          <div className="grid grid-cols-2 gap-1 text-xs">
                            <span className="text-gray-600">Investments:</span>
                            <span className="font-semibold">{territory.metrics?.investments || 0}/10</span>
                            <span className="text-gray-600">Buildings:</span>
                            <span className="font-semibold">{territory.metrics?.buildings || 0}</span>
                            <span className="text-gray-600">Population:</span>
                            <span className="font-semibold">{territory.metrics?.populationDensity || 0}/10</span>
                            <span className="text-gray-600">Livability:</span>
                            <span className="font-semibold text-green-600">{territory.metrics?.livabilityIndex || 0}/10</span>
                            <span className="text-gray-600">Crime Rate:</span>
                            <span className="font-semibold text-red-600">{territory.metrics?.crimeRate || 0}/10</span>
                            <span className="text-gray-600">Govt Infra:</span>
                            <span className="font-semibold">{territory.metrics?.govtInfra || 0}/10</span>
                          </div>
                        </div>

                        {territory.aiInsights?.aiSuggestions && territory.aiInsights.aiSuggestions.length > 0 && (
                          <div className="pt-2 border-t">
                            <h4 className="font-semibold text-xs text-purple-600 mb-1">AI Suggestions</h4>
                            <ul className="text-xs space-y-0.5 list-disc list-inside">
                              {territory.aiInsights.aiSuggestions.map((suggestion, idx) => (
                                <li key={idx} className="text-gray-700">{suggestion}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </Popup>
                    </Circle>
                    
                    {/* Rating Badge Marker at Center */}
                    {totalScore > 0 && (
                      <Marker
                        position={[territory.center.lat, territory.center.lng]}
                        icon={L.divIcon({
                          className: 'territory-rating-badge',
                          html: `
                            <div style="
                              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white;
                              padding: 8px 12px;
                              border-radius: 20px;
                              font-weight: bold;
                              font-size: 14px;
                              box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                              border: 3px solid white;
                              text-align: center;
                              min-width: 80px;
                            ">
                              ⭐ ${totalScore}
                            </div>
                          `,
                          iconSize: [100, 40],
                          iconAnchor: [50, 20]
                        })}
                      >
                        <Popup maxWidth={300}>
                          <div className="text-sm space-y-2">
                            <div className="border-b pb-2">
                              <h3 className="font-bold text-lg text-purple-700">Territory Rating</h3>
                              <div className="text-2xl font-bold text-purple-900 mt-1">⭐ {totalScore}</div>
                            </div>
                            
                            {rating?.topContributors && rating.topContributors.length > 0 && (
                              <div>
                                <h4 className="font-semibold text-xs text-gray-700 mb-2">Top Contributors:</h4>
                                <div className="space-y-1">
                                  {rating.topContributors.map((contrib, idx) => (
                                    <div key={idx} className="flex items-center justify-between text-xs bg-purple-50 p-2 rounded">
                                      <div>
                                        <span className="font-semibold">{contrib.type}</span>
                                        <span className="text-gray-500 ml-1">({contrib.count} pins)</span>
                                      </div>
                                      <div className="text-right">
                                        <div className="font-bold text-purple-700">{contrib.score}</div>
                                        <div className="text-gray-600">{contrib.percentage}%</div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </Popup>
                      </Marker>
                    )}
                  </React.Fragment>
                );
              }
              return null;
            })}
            
            {/* Pins */}
            {visiblePins.map(pin => {
              const isHighlighted = isPinInSelectedTerritory(pin);
              const icon = isHighlighted ? highlightedPinIcon : pinIcons[pin.type[0]] || pinIcons.job;
              
              return (
                <React.Fragment key={pin.id}>
                  <Marker
                    position={[pin.location.lat, pin.location.lng]}
                    icon={icon}
                  >
                    <Popup maxWidth={280}>
                      <div className="text-sm space-y-2">
                        <div className="border-b pb-2">
                          <h3 className="font-bold text-base">{pin.label}</h3>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {pin.type.map((type, idx) => (
                              <span key={idx} className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                                {type}
                              </span>
                            ))}
                          </div>
                        </div>

                        {pin.description && (
                          <div>
                            <p className="text-xs text-gray-700">{pin.description}</p>
                          </div>
                        )}

                        {pin.address && (
                          <div>
                            <span className="text-xs text-gray-600">Address: </span>
                            <span className="text-xs font-medium">{pin.address}</span>
                          </div>
                        )}

                        <div className="text-xs">
                          <span className="text-gray-600">Location: </span>
                          <span className="font-mono">{pin.location.lat.toFixed(4)}, {pin.location.lng.toFixed(4)}</span>
                        </div>

                        {pin.hasGeofence && (
                          <div className="text-xs bg-purple-50 text-purple-800 px-2 py-1 rounded">
                            🔵 Geofence: {pin.geofenceRadius}m radius
                          </div>
                        )}

                        {isHighlighted && (
                          <div className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded font-semibold">
                            📍 Inside selected territory
                          </div>
                        )}

                        <div className="pt-2 border-t text-xs text-gray-500">
                          Created by: <span className="font-medium">{pin.userName}</span>
                        </div>

                        {pin.aiInsights && (
                          <div className="pt-2 border-t">
                            <h4 className="text-xs font-semibold text-purple-600 mb-1">AI Insights</h4>
                            <div className="text-xs bg-purple-50 p-2 rounded">
                              {JSON.stringify(pin.aiInsights.insights || pin.aiInsights)}
                            </div>
                          </div>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                  {pin.hasGeofence && (
                    <Circle
                      center={[pin.location.lat, pin.location.lng]}
                      radius={pin.geofenceRadius}
                      pathOptions={{ color: 'purple', fillOpacity: 0.1 }}
                    />
                  )}
                </React.Fragment>
              );
            })}
            
            {/* Comment Markers */}
            {comments.map(comment => {
              const territory = territories.find(t => t.id === comment.territoryId);
              if (!territory || !territory.center) return null;
              
              return (
                <Marker
                  key={`comment-${comment.id}`}
                  position={[territory.center.lat, territory.center.lng]}
                  icon={commentIcon}
                >
                  <Popup maxWidth={280}>
                    <div className="text-sm space-y-2">
                      <div className="flex items-center gap-2 border-b pb-2">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                          <span className="text-xs font-bold text-purple-700">
                            {comment.userName.split(' ').map(n => n[0]).join('')}
                          </span>
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold">{comment.userName}</div>
                          <div className="text-xs text-gray-500">{territory.name}</div>
                        </div>
                      </div>
                      <div>
                        <p className="text-gray-700">{comment.text}</p>
                      </div>
                      {comment.photo && (
                        <img
                          src={comment.photo}
                          alt="Comment attachment"
                          className="w-full h-32 object-cover rounded"
                        />
                      )}
                      <div className="text-xs text-gray-400 pt-2 border-t">
                        {new Date(comment.createdAt).toLocaleDateString()}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        </div>
      </div>

      {/* Action Selection Dialog */}
      <Dialog open={showActionDialog} onOpenChange={setShowActionDialog}>
        <DialogContent className="max-w-md bg-gradient-to-br from-white to-orange-50 backdrop-blur-lg border-orange-200">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-orange-500 bg-clip-text text-transparent">
              What would you like to create?
            </DialogTitle>
            <DialogDescription>
              Choose an action to perform at the selected location
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <button
              onClick={handleCreatePin}
              className="group p-6 bg-white hover:bg-gradient-to-br hover:from-white hover:to-orange-50 rounded-xl border-2 border-orange-200 hover:border-orange-400 transition-all duration-300 hover:shadow-lg hover:scale-105"
            >
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <MapPin className="w-8 h-8 text-white" />
                </div>
                <div className="text-center">
                  <h3 className="font-bold text-gray-800">Create Pin</h3>
                  <p className="text-xs text-gray-500 mt-1">Add a location marker</p>
                </div>
              </div>
            </button>
            
            <button
              onClick={handleCreatePost}
              className="group p-6 bg-white hover:bg-gradient-to-br hover:from-white hover:to-orange-50 rounded-xl border-2 border-orange-200 hover:border-orange-400 transition-all duration-300 hover:shadow-lg hover:scale-105"
            >
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <MessageSquare className="w-8 h-8 text-white" />
                </div>
                <div className="text-center">
                  <h3 className="font-bold text-gray-800">Create Post</h3>
                  <p className="text-xs text-gray-500 mt-1">Share your thoughts</p>
                </div>
              </div>
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Community Dialog */}
      <Dialog open={showCommunityDialog} onOpenChange={setShowCommunityDialog}>
        <DialogContent className="max-w-md bg-gradient-to-br from-white to-orange-50 backdrop-blur-lg">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold bg-gradient-to-r from-orange-600 to-orange-500 bg-clip-text text-transparent">
              Create Community
            </DialogTitle>
            <DialogDescription>
              Build a community around a territory
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={async (e) => {
            e.preventDefault();
            if (!communityForm.name.trim() || !communityForm.territoryId) {
              toast.error('Please enter community name and select territory');
              return;
            }
            setLoading(true);
            try {
              const token = localStorage.getItem('token');
              await axios.post(`${BACKEND_URL}/api/communities`, {
                name: communityForm.name,
                description: communityForm.description,
                territoryId: communityForm.territoryId,
                photo: communityForm.photoPreview,
                canJoin: communityForm.canJoin
              }, { headers: { Authorization: `Bearer ${token}` }});
              toast.success('Community created successfully!');
              setCommunityForm({ name: '', description: '', territoryId: '', photo: null, photoPreview: null, canJoin: true });
              setShowCommunityDialog(false);
              loadData();
            } catch (error) {
              toast.error('Failed to create community');
            } finally {
              setLoading(false);
            }
          }} className="space-y-4">
            <div>
              <Label>Community Name *</Label>
              <Input
                required
                value={communityForm.name}
                onChange={(e) => setCommunityForm({...communityForm, name: e.target.value})}
                placeholder="e.g., Satellite Residents"
                className="border-orange-200 focus:border-orange-400"
              />
            </div>
            
            <div>
              <Label>Select Territory *</Label>
              <Select value={communityForm.territoryId} onValueChange={(val) => setCommunityForm({...communityForm, territoryId: val})}>
                <SelectTrigger className="border-orange-200 focus:border-orange-400">
                  <SelectValue placeholder="Choose territory" />
                </SelectTrigger>
                <SelectContent>
                  {territories.map(territory => (
                    <SelectItem key={territory.id} value={territory.id}>
                      {territory.name} - {territory.pincode}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Description (Optional)</Label>
              <Textarea
                value={communityForm.description}
                onChange={(e) => setCommunityForm({...communityForm, description: e.target.value})}
                placeholder="What's your community about?"
                rows={3}
                className="resize-none border-orange-200 focus:border-orange-400"
              />
            </div>

            <div>
              <Label>Community Photo (Optional)</Label>
              {!communityForm.photoPreview ? (
                <label className="flex items-center justify-center gap-2 px-4 py-2 border-2 border-dashed border-orange-300 rounded-lg cursor-pointer hover:bg-orange-50">
                  <Upload className="w-4 h-4 text-orange-600" />
                  <span className="text-sm text-orange-600">Upload Photo</span>
                  <input type="file" accept="image/*" onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      const reader = new FileReader();
                      reader.onloadend = () => {
                        setCommunityForm({...communityForm, photo: file, photoPreview: reader.result});
                      };
                      reader.readAsDataURL(file);
                    }
                  }} className="hidden" />
                </label>
              ) : (
                <div className="relative">
                  <img src={communityForm.photoPreview} alt="Preview" className="w-full h-32 object-cover rounded-lg" />
                  <button type="button" onClick={() => setCommunityForm({...communityForm, photo: null, photoPreview: null})} 
                    className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="canJoin"
                checked={communityForm.canJoin}
                onCheckedChange={(checked) => setCommunityForm({...communityForm, canJoin: checked})}
              />
              <Label htmlFor="canJoin" className="cursor-pointer">
                Allow others to join this community
              </Label>
            </div>

            <div className="flex gap-2 pt-2">
              <Button type="submit" disabled={loading} className="flex-1 bg-gradient-to-r from-orange-500 to-orange-600">
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Community'
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCommunityDialog(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Create Territory Dialog */}
      <Dialog open={showTerritoryDialog} onOpenChange={setShowTerritoryDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Territory</DialogTitle>
            <DialogDescription>
              Enter territory details. A 5km diameter circle will be created around the pincode center.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateTerritory} className="space-y-4">
            <div>
              <Label>Territory Name</Label>
              <Input
                required
                value={territoryForm.name}
                onChange={(e) => setTerritoryForm({ ...territoryForm, name: e.target.value })}
                placeholder="e.g., Satellite Area"
              />
            </div>
            
            <div>
              <Label>Pincode (6 digits)</Label>
              <Input
                required
                type="text"
                maxLength={6}
                pattern="[0-9]{6}"
                value={territoryForm.pincode}
                onChange={(e) => setTerritoryForm({ ...territoryForm, pincode: e.target.value })}
                placeholder="380015"
              />
              <p className="text-xs text-gray-500 mt-1">
                A 5km diameter circle will be created around this pincode
              </p>
            </div>

            <div className="flex gap-2 pt-2">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Territory'
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowTerritoryDialog(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Create Pin Dialog */}
      <Dialog open={showPinDialog} onOpenChange={(open) => {
        setShowPinDialog(open);
        if (!open) {
          // Reset form when closing (keep location)
          setPinForm({
            ...pinForm,
            type: [],
            label: '',
            description: '',
            hasGeofence: false,
            geofenceRadius: 1000,
            territoryId: '',
            generateAIInsights: false
          });
        }
      }}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Pin</DialogTitle>
            <DialogDescription>
              <div className="flex items-center gap-2 text-blue-600 font-semibold">
                <span>📍 Step 1: Drag the red marker on map to select location</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600 text-xs mt-1">
                <span>Step 2: Fill in the details below</span>
              </div>
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitPin} className="space-y-4">
            <div>
              <Label className="text-sm font-semibold">📍 Selected Location</Label>
              <div className="mt-2 p-3 bg-blue-50 border-2 border-blue-200 rounded-lg">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Latitude:</span>
                    <div className="font-mono font-bold text-blue-900">{pinForm.location.lat.toFixed(6)}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Longitude:</span>
                    <div className="font-mono font-bold text-blue-900">{pinForm.location.lng.toFixed(6)}</div>
                  </div>
                </div>
                <div className="mt-2 text-xs text-blue-700 flex items-center gap-1">
                  <span>💡</span>
                  <span>Drag the <strong className="text-red-600">RED MARKER</strong> on the map to change location</span>
                </div>
              </div>
            </div>

            <div>
              <Label>Pin Types (select multiple)</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {PIN_TYPES.map(type => (
                  <div key={type.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`pin-type-${type.value}`}
                      checked={pinForm.type.includes(type.value)}
                      onCheckedChange={(checked) => {
                        setPinForm({
                          ...pinForm,
                          type: checked
                            ? [...pinForm.type, type.value]
                            : pinForm.type.filter(t => t !== type.value)
                        });
                      }}
                    />
                    <Label
                      htmlFor={`pin-type-${type.value}`}
                      className="text-sm cursor-pointer"
                    >
                      {type.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label>Label</Label>
              <Input
                required
                value={pinForm.label}
                onChange={(e) => setPinForm({ ...pinForm, label: e.target.value })}
                placeholder="Pin name"
              />
            </div>

            <div>
              <Label>Description (Optional)</Label>
              <Input
                value={pinForm.description}
                onChange={(e) => setPinForm({ ...pinForm, description: e.target.value })}
                placeholder="Additional details"
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="hasGeofence"
                checked={pinForm.hasGeofence}
                onCheckedChange={(checked) => setPinForm({ ...pinForm, hasGeofence: checked })}
              />
              <Label htmlFor="hasGeofence">Enable Geofence</Label>
            </div>

            {pinForm.hasGeofence && (
              <div>
                <Label>Geofence Radius (meters)</Label>
                <Input
                  type="number"
                  value={pinForm.geofenceRadius}
                  onChange={(e) => setPinForm({ ...pinForm, geofenceRadius: parseInt(e.target.value) })}
                />
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Pin'
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowPinDialog(false);
                  setIsPickingLocation(false);
                }}
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Create Post Dialog */}
      <Dialog open={showPostDialog} onOpenChange={setShowPostDialog}>
        <DialogContent className="max-w-md bg-gradient-to-br from-white to-orange-50 backdrop-blur-lg">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold">Create Post</DialogTitle>
            <DialogDescription>
              Share your thoughts at this location
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={async (e) => {
            e.preventDefault();
            if (!postForm.text.trim() || !postForm.communityId) {
              toast.error('Please enter text and select a community');
              return;
            }
            try {
              const token = localStorage.getItem('token');
              await axios.post(`${BACKEND_URL}/api/posts`, {
                text: postForm.text,
                communityId: postForm.communityId,
                location: pinForm.location,
                photo: postForm.photoPreview
              }, { headers: { Authorization: `Bearer ${token}` }});
              toast.success('Post created successfully!');
              setPostForm({ text: '', communityId: '', photo: null, photoPreview: null });
              setShowPostDialog(false);
              loadData();
            } catch (error) {
              toast.error('Failed to create post');
            }
          }} className="space-y-4">
            <div>
              <Label>Select Community</Label>
              <Select value={postForm.communityId} onValueChange={(val) => setPostForm({...postForm, communityId: val})}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose community" />
                </SelectTrigger>
                <SelectContent>
                  {communities.map(community => (
                    <SelectItem key={community.id} value={community.id}>
                      {community.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Your Thoughts</Label>
              <Textarea
                value={postForm.text}
                onChange={(e) => setPostForm({...postForm, text: e.target.value})}
                placeholder="Share what's on your mind..."
                rows={4}
                className="resize-none"
              />
            </div>

            <div>
              <Label>Attach Photo (Optional)</Label>
              {!postForm.photoPreview ? (
                <label className="flex items-center justify-center gap-2 px-4 py-2 border-2 border-dashed border-orange-300 rounded-lg cursor-pointer hover:bg-orange-50">
                  <Upload className="w-4 h-4 text-orange-600" />
                  <span className="text-sm text-orange-600">Upload Photo</span>
                  <input type="file" accept="image/*" onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      const reader = new FileReader();
                      reader.onloadend = () => {
                        setPostForm({...postForm, photo: file, photoPreview: reader.result});
                      };
                      reader.readAsDataURL(file);
                    }
                  }} className="hidden" />
                </label>
              ) : (
                <div className="relative">
                  <img src={postForm.photoPreview} alt="Preview" className="w-full h-32 object-cover rounded-lg" />
                  <button type="button" onClick={() => setPostForm({...postForm, photo: null, photoPreview: null})} 
                    className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            <Button type="submit" className="w-full bg-gradient-to-r from-orange-500 to-orange-600">
              <MessageSquare className="w-4 h-4 mr-2" />
              Create Post
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* Filter Dialog */}
      <Dialog open={showFilterDialog} onOpenChange={setShowFilterDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Filter Pins by Type</DialogTitle>
            <DialogDescription>
              Select pin types to show on the map
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            {PIN_TYPES.map(type => (
              <div key={type.value} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                <Label htmlFor={`filter-${type.value}`} className="cursor-pointer flex-1">
                  {type.label}
                </Label>
                <Checkbox
                  id={`filter-${type.value}`}
                  checked={activeFilters.includes(type.value)}
                  onCheckedChange={() => toggleFilter(type.value)}
                />
              </div>
            ))}
            <div className="flex gap-2 pt-2">
              <Button
                onClick={() => setActiveFilters(PIN_TYPES.map(t => t.value))}
                variant="outline"
                className="flex-1"
              >
                Select All
              </Button>
              <Button
                onClick={() => setActiveFilters([])}
                variant="outline"
                className="flex-1"
              >
                Clear All
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
