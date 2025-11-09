import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { MapContainer, TileLayer, Circle, Marker, Popup } from 'react-leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { toast } from 'sonner';
import { 
  MapPin, Users, Building2, Lightbulb, TrendingUp, 
  Shield, Calendar, Phone, Mail, Award, ChevronRight,
  Filter, Download, Star, MessageSquare, ThumbsUp
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const TerritoryProfile = () => {
  const { territoryId } = useParams();
  const [territory, setTerritory] = useState(null);
  const [stats, setStats] = useState({});
  const [professionals, setProfessionals] = useState([]);
  const [projects, setProjects] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [events, setEvents] = useState([]);
  const [posts, setPosts] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTerritoryProfile();
  }, [territoryId]);

  const loadTerritoryProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [profileRes, professionalsRes, projectsRes, opportunitiesRes, eventsRes, postsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/territories/${territoryId}/profile`, { headers }),
        axios.get(`${BACKEND_URL}/api/professionals?territory_id=${territoryId}`, { headers }),
        axios.get(`${BACKEND_URL}/api/projects?territory_id=${territoryId}`, { headers }),
        axios.get(`${BACKEND_URL}/api/opportunities?territory_id=${territoryId}`, { headers }),
        axios.get(`${BACKEND_URL}/api/events?territory_id=${territoryId}`, { headers }),
        axios.get(`${BACKEND_URL}/api/posts`, { headers })
      ]);

      setTerritory(profileRes.data.territory);
      setStats(profileRes.data.stats);
      setProfessionals(professionalsRes.data);
      setProjects(projectsRes.data);
      setOpportunities(opportunitiesRes.data);
      setEvents(eventsRes.data);
      setPosts(postsRes.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load territory profile');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading territory profile...</p>
        </div>
      </div>
    );
  }

  if (!territory) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-600">Territory not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-orange-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-600 rounded-xl flex items-center justify-center">
                <MapPin className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-orange-500 bg-clip-text text-transparent">
                  {territory.name}
                </h1>
                <div className="flex items-center gap-3 mt-1">
                  <Badge variant="outline" className="border-orange-300">
                    {territory.pincode}
                  </Badge>
                  <Badge variant="outline" className="border-orange-300">
                    {territory.zone}
                  </Badge>
                  {territory.rating && territory.rating.totalScore > 0 && (
                    <Badge className="bg-gradient-to-r from-purple-500 to-purple-600">
                      ⭐ {territory.rating.totalScore}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button variant="outline" className="border-orange-300 hover:bg-orange-50">
                <Star className="w-4 h-4 mr-2" />
                Follow
              </Button>
              <Button className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700">
                <MessageSquare className="w-4 h-4 mr-2" />
                Join Community
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Stats */}
          <div className="col-span-3 space-y-4">
            <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
              <CardHeader>
                <CardTitle className="text-sm text-gray-600">Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium">Professionals</span>
                  </div>
                  <Badge className="bg-orange-600">{stats.professionals || 0}</Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium">Projects</span>
                  </div>
                  <Badge className="bg-orange-600">{stats.projects || 0}</Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium">Opportunities</span>
                  </div>
                  <Badge className="bg-orange-600">{stats.opportunities || 0}</Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium">Active Posts</span>
                  </div>
                  <Badge className="bg-orange-600">{stats.posts || 0}</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Mini Map */}
            <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
              <CardHeader>
                <CardTitle className="text-sm text-gray-600">Location</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-48 rounded-lg overflow-hidden">
                  <MapContainer
                    center={[territory.center.lat, territory.center.lng]}
                    zoom={13}
                    className="w-full h-full"
                  >
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <Circle
                      center={[territory.center.lat, territory.center.lng]}
                      radius={territory.radius || 2500}
                      pathOptions={{ color: '#f97316', fillOpacity: 0.2 }}
                    />
                  </MapContainer>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  <p>Lat: {territory.center.lat.toFixed(6)}</p>
                  <p>Lng: {territory.center.lng.toFixed(6)}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Area - Tabs */}
          <div className="col-span-9">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid grid-cols-7 w-full bg-white/80 backdrop-blur-lg border border-orange-200">
                <TabsTrigger value="overview" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white">
                  <MapPin className="w-4 h-4 mr-2" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="professionals" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white">
                  <Users className="w-4 h-4 mr-2" />
                  Professionals
                </TabsTrigger>
                <TabsTrigger value="projects" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white">
                  <Building2 className="w-4 h-4 mr-2" />
                  Projects
                </TabsTrigger>
                <TabsTrigger value="opportunities" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white">
                  <Lightbulb className="w-4 h-4 mr-2" />
                  Opportunities
                </TabsTrigger>
                <TabsTrigger value="trendings" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Trendings
                </TabsTrigger>
                <TabsTrigger value="governance" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white">
                  <Shield className="w-4 h-4 mr-2" />
                  Governance
                </TabsTrigger>
                <TabsTrigger value="events" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white">
                  <Calendar className="w-4 h-4 mr-2" />
                  Events
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="mt-6 space-y-4">
                <div className="grid grid-cols-4 gap-4">
                  <Card className="bg-gradient-to-br from-white to-orange-50 backdrop-blur-lg border-orange-200 hover:shadow-lg transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">Active Projects</p>
                          <h3 className="text-3xl font-bold text-orange-600 mt-1">{projects.length}</h3>
                        </div>
                        <Building2 className="w-12 h-12 text-orange-400 opacity-50" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-white to-orange-50 backdrop-blur-lg border-orange-200 hover:shadow-lg transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">Professionals</p>
                          <h3 className="text-3xl font-bold text-orange-600 mt-1">{professionals.length}</h3>
                        </div>
                        <Users className="w-12 h-12 text-orange-400 opacity-50" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-white to-orange-50 backdrop-blur-lg border-orange-200 hover:shadow-lg transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">Hot Leads</p>
                          <h3 className="text-3xl font-bold text-orange-600 mt-1">{opportunities.length}</h3>
                        </div>
                        <Lightbulb className="w-12 h-12 text-orange-400 opacity-50" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-white to-orange-50 backdrop-blur-lg border-orange-200 hover:shadow-lg transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">Local Pulses</p>
                          <h3 className="text-3xl font-bold text-orange-600 mt-1">{posts.length}</h3>
                        </div>
                        <TrendingUp className="w-12 h-12 text-orange-400 opacity-50" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle>Territory Insights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="p-4 bg-orange-50 rounded-lg">
                        <h4 className="font-semibold mb-2">AI Rating</h4>
                        {territory.rating && territory.rating.topContributors && (
                          <div className="space-y-2">
                            {territory.rating.topContributors.map((contrib, idx) => (
                              <div key={idx} className="flex justify-between text-sm">
                                <span>{contrib.type}</span>
                                <span className="font-bold text-orange-600">{contrib.score}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="p-4 bg-orange-50 rounded-lg">
                        <h4 className="font-semibold mb-2">Quality Metrics</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Livability</span>
                            <span className="font-bold text-orange-600">{territory.metrics?.livabilityIndex || 0}/10</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Infrastructure</span>
                            <span className="font-bold text-orange-600">{territory.metrics?.govtInfra || 0}/10</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Safety</span>
                            <span className="font-bold text-orange-600">{10 - (territory.metrics?.crimeRate || 0)}/10</span>
                          </div>
                        </div>
                      </div>

                      <div className="p-4 bg-orange-50 rounded-lg">
                        <h4 className="font-semibold mb-2">Market Activity</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Investments</span>
                            <span className="font-bold text-orange-600">{territory.metrics?.investments || 0}/10</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Buildings</span>
                            <span className="font-bold text-orange-600">{territory.metrics?.buildings || 0}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Population</span>
                            <span className="font-bold text-orange-600">{territory.metrics?.populationDensity || 0}/10</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Professionals Tab */}
              <TabsContent value="professionals" className="mt-6">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Registered Professionals</CardTitle>
                    <Button variant="outline" size="sm">
                      <Filter className="w-4 h-4 mr-2" />
                      Filter
                    </Button>
                  </CardHeader>
                  <CardContent>
                    {professionals.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No professionals registered yet</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-4">
                        {professionals.map((prof) => (
                          <Card key={prof.id} className="border-orange-100 hover:shadow-md transition-shadow">
                            <CardContent className="p-4">
                              <div className="flex items-start gap-3">
                                <Avatar>
                                  <AvatarImage src={prof.photo} />
                                  <AvatarFallback className="bg-orange-100 text-orange-600">
                                    {prof.name.split(' ').map(n => n[0]).join('')}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-semibold">{prof.name}</h4>
                                    {prof.verified && <Award className="w-4 h-4 text-orange-500" />}
                                  </div>
                                  <p className="text-sm text-gray-600">{prof.professionType}</p>
                                  <div className="flex gap-2 mt-3">
                                    {prof.phone && (
                                      <Button size="sm" variant="outline">
                                        <Phone className="w-3 h-3 mr-1" />
                                        Call
                                      </Button>
                                    )}
                                    {prof.email && (
                                      <Button size="sm" variant="outline">
                                        <Mail className="w-3 h-3 mr-1" />
                                        Email
                                      </Button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Projects Tab */}
              <TabsContent value="projects" className="mt-6">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle>Societies & Projects</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {projects.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Building2 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No projects listed yet</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {projects.map((project) => (
                          <Card key={project.id} className="border-orange-100 hover:shadow-md transition-shadow">
                            <CardContent className="p-4">
                              <div className="flex justify-between items-start">
                                <div>
                                  <h4 className="font-bold text-lg">{project.name}</h4>
                                  <p className="text-sm text-gray-600">by {project.developerName}</p>
                                  <div className="flex gap-2 mt-2">
                                    <Badge className={
                                      project.status === 'Ready' ? 'bg-green-500' :
                                      project.status === 'Under Construction' ? 'bg-orange-500' :
                                      'bg-blue-500'
                                    }>
                                      {project.status}
                                    </Badge>
                                    <Badge variant="outline">{project.configuration}</Badge>
                                  </div>
                                  <p className="mt-2 font-semibold text-orange-600">{project.priceRange}</p>
                                </div>
                                {project.brochureUrl && (
                                  <Button size="sm" variant="outline">
                                    <Download className="w-4 h-4 mr-2" />
                                    Brochure
                                  </Button>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Opportunities Tab */}
              <TabsContent value="opportunities" className="mt-6">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle>Live Opportunities</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {opportunities.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Lightbulb className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No opportunities available</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {opportunities.map((opp) => (
                          <Card key={opp.id} className="border-orange-100 hover:shadow-md transition-shadow">
                            <CardContent className="p-4">
                              <div className="flex justify-between items-start">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-semibold">{opp.title}</h4>
                                    {opp.isNew && <Badge className="bg-green-500">New</Badge>}
                                    <Badge variant="outline">{opp.type}</Badge>
                                  </div>
                                  <p className="text-sm text-gray-600 mt-1">{opp.description}</p>
                                </div>
                                <div className="flex gap-2">
                                  <Button size="sm" className="bg-gradient-to-r from-orange-500 to-orange-600">
                                    Claim
                                  </Button>
                                  <Button size="sm" variant="outline">
                                    Refer
                                  </Button>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Trendings Tab */}
              <TabsContent value="trendings" className="mt-6">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle>Trendings / Pulses / News</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {posts.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <TrendingUp className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No posts yet</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {posts.map((post) => (
                          <Card key={post.id} className="border-orange-100">
                            <CardContent className="p-4">
                              <div className="flex items-start gap-3">
                                <Avatar>
                                  <AvatarFallback className="bg-orange-100 text-orange-600">
                                    {post.userName.split(' ').map(n => n[0]).join('')}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-semibold">{post.userName}</h4>
                                    <span className="text-xs text-gray-500">
                                      {new Date(post.createdAt).toLocaleDateString()}
                                    </span>
                                  </div>
                                  <p className="text-sm mt-2">{post.text}</p>
                                  {post.photo && (
                                    <img src={post.photo} alt="Post" className="mt-3 rounded-lg max-h-64 object-cover" />
                                  )}
                                  <div className="flex gap-4 mt-3">
                                    <Button size="sm" variant="ghost">
                                      <ThumbsUp className="w-4 h-4 mr-1" />
                                      Like
                                    </Button>
                                    <Button size="sm" variant="ghost">
                                      <MessageSquare className="w-4 h-4 mr-1" />
                                      Comment
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Governance Tab */}
              <TabsContent value="governance" className="mt-6">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle>Territory Governance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-12 text-gray-500">
                      <Shield className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <p>Governance panel coming soon</p>
                      <Button className="mt-4 bg-gradient-to-r from-orange-500 to-orange-600">
                        Join Governance
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Events Tab */}
              <TabsContent value="events" className="mt-6">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle>Upcoming Events</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {events.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Calendar className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No events scheduled</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {events.map((event) => (
                          <Card key={event.id} className="border-orange-100 hover:shadow-md transition-shadow">
                            <CardContent className="p-4">
                              <div className="flex justify-between items-start">
                                <div>
                                  <h4 className="font-bold">{event.title}</h4>
                                  <p className="text-sm text-gray-600 mt-1">
                                    {new Date(event.date).toLocaleDateString()} • {event.location}
                                  </p>
                                  <p className="text-sm text-gray-600">Organized by: {event.organizer}</p>
                                  <Badge className="mt-2" variant={event.status === 'upcoming' ? 'default' : 'secondary'}>
                                    {event.status}
                                  </Badge>
                                </div>
                                <Button size="sm" className="bg-gradient-to-r from-orange-500 to-orange-600">
                                  RSVP
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};
