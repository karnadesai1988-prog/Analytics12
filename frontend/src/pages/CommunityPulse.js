import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { toast } from 'sonner';
import { MessageSquare, Send, Upload, X, MapPin, User } from 'lucide-react';
import axios from 'axios';
import L from 'leaflet';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const AHMEDABAD_CENTER = [23.0225, 72.5714];

// Comment marker icon
const commentIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34]
});

export const CommunityPulse = () => {
  const [territories, setTerritories] = useState([]);
  const [comments, setComments] = useState([]);
  const [selectedTerritory, setSelectedTerritory] = useState('');
  const [newComment, setNewComment] = useState('');
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [communityUsers, setCommunityUsers] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedTerritory) {
      loadCommentsByTerritory();
    }
  }, [selectedTerritory]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [territoriesRes, commentsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/territories`, { headers }),
        axios.get(`${BACKEND_URL}/api/comments`, { headers })
      ]);
      
      setTerritories(territoriesRes.data);
      setComments(commentsRes.data);
      
      // Set first territory as default
      if (territoriesRes.data.length > 0) {
        setSelectedTerritory(territoriesRes.data[0].id);
      }
      
      // Extract unique users from comments
      const users = commentsRes.data.map(c => ({
        id: c.userId,
        name: c.userName,
        initials: c.userName.split(' ').map(n => n[0]).join('')
      }));
      const uniqueUsers = Array.from(new Map(users.map(u => [u.id, u])).values());
      setCommunityUsers(uniqueUsers);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const loadCommentsByTerritory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/comments`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { territory_id: selectedTerritory }
      });
      
      setComments(response.data);
    } catch (error) {
      console.error('Failed to load comments:', error);
    }
  };

  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Photo size should be less than 5MB');
        return;
      }
      setSelectedPhoto(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemovePhoto = () => {
    setSelectedPhoto(null);
    setPhotoPreview(null);
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    
    if (!newComment.trim()) {
      toast.error('Please enter a comment');
      return;
    }
    
    if (!selectedTerritory) {
      toast.error('Please select a territory');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');

      const commentData = {
        territoryId: selectedTerritory,
        text: newComment,
        useAI: false
      };

      // If photo is selected, convert to base64 and include
      if (selectedPhoto) {
        commentData.photo = photoPreview;
      }

      await axios.post(`${BACKEND_URL}/api/comments`, commentData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Comment posted successfully!');
      setNewComment('');
      handleRemovePhoto();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to post comment');
    } finally {
      setLoading(false);
    }
  };

  // Get comment location based on zone (approximate center of zone)
  const getZoneCenter = (zone) => {
    const zoneCenters = {
      'Central Zone': [23.0350, 72.5850],
      'West Zone': [23.0113, 72.5860],
      'East Zone': [23.0400, 72.6200],
      'North Zone': [23.0650, 72.5700],
      'South Zone': [22.9800, 72.5700],
      'Satellite Zone': [23.0200, 72.5000],
      'Bodakdev Zone': [23.0390, 72.5100],
      'Vastrapur Zone': [23.0300, 72.5250],
      'Maninagar Zone': [23.0100, 72.6000],
      'Navrangpura Zone': [23.0380, 72.5600]
    };
    return zoneCenters[zone] || AHMEDABAD_CENTER;
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <MessageSquare className="w-8 h-8 text-primary" />
              Community Pulse
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Share feedback, report issues, and connect with your community
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Full Width - Comment Form & List */}
        <div className="max-w-4xl mx-auto p-6 overflow-y-auto h-full">
          <div className="p-4 space-y-4">
            {/* Post Comment Form */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Share Your Thoughts</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmitComment} className="space-y-3">
                  <div>
                    <Label>Select Zone</Label>
                    <Select value={selectedZone} onValueChange={setSelectedZone}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose zone" />
                      </SelectTrigger>
                      <SelectContent>
                        {ZONES.map(zone => (
                          <SelectItem key={zone} value={zone}>
                            {zone}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label>Your Comment</Label>
                    <Textarea
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder="Share feedback, report typos, or suggest improvements..."
                      rows={3}
                      className="resize-none"
                    />
                  </div>

                  {/* Photo Upload */}
                  <div>
                    <Label>Attach Photo (Optional)</Label>
                    <div className="mt-2">
                      {!photoPreview ? (
                        <label className="flex items-center justify-center gap-2 px-4 py-2 border-2 border-dashed rounded-lg cursor-pointer hover:bg-gray-50">
                          <Upload className="w-4 h-4" />
                          <span className="text-sm">Upload Photo</span>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handlePhotoSelect}
                            className="hidden"
                          />
                        </label>
                      ) : (
                        <div className="relative">
                          <img
                            src={photoPreview}
                            alt="Preview"
                            className="w-full h-32 object-cover rounded-lg"
                          />
                          <button
                            type="button"
                            onClick={handleRemovePhoto}
                            className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <Button type="submit" disabled={loading} className="w-full">
                    <Send className="w-4 h-4 mr-2" />
                    {loading ? 'Posting...' : 'Post Comment'}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Community Users */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Community Members ({communityUsers.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {communityUsers.map(user => (
                    <div key={user.id} className="flex items-center gap-2 bg-gray-100 px-3 py-1 rounded-full">
                      <Avatar className="w-6 h-6">
                        <AvatarFallback className="text-xs">{user.initials}</AvatarFallback>
                      </Avatar>
                      <span className="text-xs">{user.name}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Comments List */}
            <div className="space-y-3">
              <h3 className="font-semibold text-sm text-gray-700">
                Recent Comments ({comments.length})
              </h3>
              {comments.map(comment => {
                const territory = territories.find(t => t.id === comment.territoryId);
                return (
                  <Card key={comment.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-3">
                      <div className="flex items-start gap-2">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="text-xs">
                            {comment.userName.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">{comment.userName}</span>
                            {territory && (
                              <span className="text-xs text-gray-500">• {territory.zone}</span>
                            )}
                          </div>
                          <p className="text-sm text-gray-700 mt-1">{comment.text}</p>
                          {comment.photo && (
                            <img
                              src={comment.photo}
                              alt="Comment attachment"
                              className="mt-2 w-full h-32 object-cover rounded"
                            />
                          )}
                          <span className="text-xs text-gray-400 mt-1 block">
                            {new Date(comment.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Side - Map with Comment Markers */}
        <div className="flex-1 relative">
          <MapContainer
            center={AHMEDABAD_CENTER}
            zoom={12}
            className="w-full h-full"
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            
            {/* Territory Circles */}
            {territories.map(territory => (
              territory.center && (
                <Circle
                  key={territory.id}
                  center={[territory.center.lat, territory.center.lng]}
                  radius={territory.radius || 2500}
                  pathOptions={{
                    color: '#3b82f6',
                    weight: 2,
                    fillOpacity: 0.1
                  }}
                />
              )
            ))}
            
            {/* Comment Markers */}
            {comments.map(comment => {
              const territory = territories.find(t => t.id === comment.territoryId);
              const position = territory?.center 
                ? [territory.center.lat, territory.center.lng]
                : getZoneCenter(comment.zone || territory?.zone || 'Central Zone');
              
              return (
                <Marker
                  key={comment.id}
                  position={position}
                  icon={commentIcon}
                >
                  <Popup maxWidth={280}>
                    <div className="text-sm">
                      <div className="flex items-center gap-2 mb-2">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="text-xs">
                            {comment.userName.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-semibold">{comment.userName}</div>
                          {territory && (
                            <div className="text-xs text-gray-500">{territory.zone}</div>
                          )}
                        </div>
                      </div>
                      <p className="text-gray-700">{comment.text}</p>
                      {comment.photo && (
                        <img
                          src={comment.photo}
                          alt="Comment"
                          className="mt-2 w-full h-24 object-cover rounded"
                        />
                      )}
                      <div className="text-xs text-gray-400 mt-2">
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
    </div>
  );
};
