import React, { useEffect, useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  MessageSquare, Users, Plus, X, Upload, Send,
  Eye, TrendingUp, ThumbsUp, MessageCircle
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const Community = () => {
  const [communities, setCommunities] = useState([]);
  const [territories, setTerritories] = useState([]);
  const [selectedCommunity, setSelectedCommunity] = useState(null);
  const [expandedCommunity, setExpandedCommunity] = useState(null);
  const [posts, setPosts] = useState([]);
  const [communityMembers, setCommunityMembers] = useState([]);
  
  // Create Community Dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newCommunity, setNewCommunity] = useState({
    name: '',
    description: '',
    territoryId: '',
    photo: null,
    canJoin: true
  });
  const [photoPreview, setPhotoPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (expandedCommunity) {
      loadCommunityPosts(expandedCommunity.id);
      loadCommunityMembers(expandedCommunity.id);
    }
  }, [expandedCommunity]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [communitiesRes, territoriesRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/communities`, { headers }),
        axios.get(`${BACKEND_URL}/api/territories`, { headers })
      ]);
      
      setCommunities(communitiesRes.data);
      setTerritories(territoriesRes.data);
    } catch (error) {
      toast.error('Failed to load communities');
    }
  };

  const loadCommunityPosts = async (communityId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/posts`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { community_id: communityId }
      });
      setPosts(response.data);
    } catch (error) {
      console.error('Failed to load posts:', error);
    }
  };

  const loadCommunityMembers = async (communityId) => {
    try {
      const community = communities.find(c => c.id === communityId);
      if (community) {
        // For now, just show member count
        // In production, you'd fetch actual user details
        setCommunityMembers(community.members || []);
      }
    } catch (error) {
      console.error('Failed to load members:', error);
    }
  };

  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Photo size should be less than 5MB');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result);
        setNewCommunity({ ...newCommunity, photo: reader.result });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCreateCommunity = async (e) => {
    e.preventDefault();
    
    if (!newCommunity.name.trim()) {
      toast.error('Please enter community name');
      return;
    }
    
    if (!newCommunity.territoryId) {
      toast.error('Please select a territory');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/communities`, newCommunity, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Community created successfully!');
      setShowCreateDialog(false);
      setNewCommunity({ name: '', description: '', territoryId: '', photo: null, canJoin: true });
      setPhotoPreview(null);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create community');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinCommunity = async (communityId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/communities/${communityId}/join`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Joined community successfully!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to join community');
    }
  };

  const handleViewCommunity = (community) => {
    setExpandedCommunity(community);
  };

  const handleCloseCommunity = () => {
    setExpandedCommunity(null);
    setPosts([]);
    setCommunityMembers([]);
  };

  const getTerritoryName = (territoryId) => {
    const territory = territories.find(t => t.id === territoryId);
    return territory ? `${territory.name} (${territory.zone})` : 'Unknown Territory';
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gradient-to-br from-gray-50 to-orange-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-500 bg-clip-text text-transparent">
              <MessageSquare className="w-8 h-8 text-blue-500" />
              Community
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Connect with communities in different territories
            </p>
          </div>
          <Button 
            onClick={() => setShowCreateDialog(true)}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Community
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {!expandedCommunity ? (
          // Community Cards Grid
          <div className="max-w-7xl mx-auto">
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-1">All Communities ({communities.length})</h2>
              <p className="text-sm text-gray-500">Browse and join communities across territories</p>
            </div>
            
            {communities.length === 0 ? (
              <div className="text-center py-20">
                <MessageSquare className="w-20 h-20 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 mb-4">No communities yet</p>
                <Button 
                  onClick={() => setShowCreateDialog(true)}
                  className="bg-gradient-to-r from-blue-500 to-blue-600"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create First Community
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {communities.map((community) => (
                  <Card key={community.id} className="bg-white/80 backdrop-blur-lg border-orange-200 hover:shadow-lg transition-all hover:scale-105">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg flex items-center gap-2">
                            {community.photo && (
                              <img 
                                src={community.photo} 
                                alt={community.name}
                                className="w-10 h-10 rounded-full object-cover"
                              />
                            )}
                            {community.name}
                          </CardTitle>
                          <Badge variant="outline" className="mt-2 border-orange-300">
                            {getTerritoryName(community.territoryId)}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                        {community.description || 'No description provided'}
                      </p>
                      
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-1 text-sm text-gray-500">
                          <Users className="w-4 h-4" />
                          <span>{community.members?.length || 0} members</span>
                        </div>
                        <Badge className="bg-green-500">
                          {community.canJoin ? 'Open' : 'Closed'}
                        </Badge>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          onClick={() => handleViewCommunity(community)}
                          variant="outline"
                          className="flex-1 border-orange-300 hover:bg-orange-50"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View
                        </Button>
                        {community.canJoin && (
                          <Button 
                            onClick={() => handleJoinCommunity(community.id)}
                            className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600"
                          >
                            <Plus className="w-4 h-4 mr-2" />
                            Join
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ) : (
          // Expanded Community View
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  {expandedCommunity.photo && (
                    <img 
                      src={expandedCommunity.photo} 
                      alt={expandedCommunity.name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  )}
                  {expandedCommunity.name}
                </h2>
                <Badge variant="outline" className="mt-2 border-orange-300">
                  {getTerritoryName(expandedCommunity.territoryId)}
                </Badge>
              </div>
              <Button onClick={handleCloseCommunity} variant="outline">
                <X className="w-4 h-4 mr-2" />
                Back to Communities
              </Button>
            </div>

            <div className="grid grid-cols-12 gap-6">
              {/* Main Content - Posts */}
              <div className="col-span-8 space-y-4">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <MessageCircle className="w-5 h-5 text-blue-500" />
                      Community Posts ({posts.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {posts.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <MessageCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No posts yet in this community</p>
                        <p className="text-sm mt-2">Go to the map to create a new post</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {posts.map((post) => (
                          <Card key={post.id} className="border-blue-100">
                            <CardContent className="p-4">
                              <div className="flex items-start gap-3">
                                <Avatar>
                                  <AvatarFallback className="bg-blue-100 text-blue-600">
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
                                    <img 
                                      src={post.photo} 
                                      alt="Post" 
                                      className="mt-3 rounded-lg max-h-64 object-cover w-full" 
                                    />
                                  )}
                                  <div className="flex gap-4 mt-3">
                                    <Button size="sm" variant="ghost">
                                      <ThumbsUp className="w-4 h-4 mr-1" />
                                      Like
                                    </Button>
                                    <Button size="sm" variant="ghost">
                                      <MessageCircle className="w-4 h-4 mr-1" />
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
              </div>

              {/* Sidebar - Community Info */}
              <div className="col-span-4 space-y-4">
                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle className="text-sm text-gray-600">About</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-700">
                      {expandedCommunity.description || 'No description provided'}
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Users className="w-4 h-4 text-blue-500" />
                      Active Members ({communityMembers.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {communityMembers.length === 0 ? (
                      <p className="text-sm text-gray-500">No members yet</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {communityMembers.slice(0, 10).map((memberId, idx) => (
                          <Avatar key={idx} className="w-8 h-8">
                            <AvatarFallback className="text-xs bg-blue-100 text-blue-600">
                              U{idx + 1}
                            </AvatarFallback>
                          </Avatar>
                        ))}
                        {communityMembers.length > 10 && (
                          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-semibold">
                            +{communityMembers.length - 10}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="bg-white/80 backdrop-blur-lg border-orange-200">
                  <CardHeader>
                    <CardTitle className="text-sm text-gray-600">Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button 
                      onClick={() => window.location.href = '/territories'}
                      className="w-full bg-gradient-to-r from-blue-500 to-blue-600"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Post on Map
                    </Button>
                    <Button 
                      variant="outline"
                      className="w-full border-orange-300 hover:bg-orange-50"
                    >
                      <TrendingUp className="w-4 h-4 mr-2" />
                      View Territory
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Community Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Community</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateCommunity} className="space-y-4">
            <div>
              <Label>Community Name *</Label>
              <Input
                value={newCommunity.name}
                onChange={(e) => setNewCommunity({ ...newCommunity, name: e.target.value })}
                placeholder="Enter community name"
                required
              />
            </div>

            <div>
              <Label>Territory *</Label>
              <select
                value={newCommunity.territoryId}
                onChange={(e) => setNewCommunity({ ...newCommunity, territoryId: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="">Select territory</option>
                {territories.map(territory => (
                  <option key={territory.id} value={territory.id}>
                    {territory.name} ({territory.zone})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label>Description</Label>
              <Textarea
                value={newCommunity.description}
                onChange={(e) => setNewCommunity({ ...newCommunity, description: e.target.value })}
                placeholder="Describe your community..."
                rows={3}
              />
            </div>

            <div>
              <Label>Community Photo (Optional)</Label>
              <div className="mt-2">
                {!photoPreview ? (
                  <label className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer hover:bg-gray-50">
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
                      onClick={() => {
                        setPhotoPreview(null);
                        setNewCommunity({ ...newCommunity, photo: null });
                      }}
                      className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={newCommunity.canJoin}
                onChange={(e) => setNewCommunity({ ...newCommunity, canJoin: e.target.checked })}
                id="canJoin"
              />
              <Label htmlFor="canJoin">Allow anyone to join</Label>
            </div>

            <div className="flex gap-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setShowCreateDialog(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={loading}
                className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600"
              >
                {loading ? 'Creating...' : 'Create Community'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};
