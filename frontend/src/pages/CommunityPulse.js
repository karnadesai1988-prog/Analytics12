import React, { useEffect, useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { toast } from 'sonner';
import { MessageSquare, Send, Upload, X, User } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <MessageSquare className="w-8 h-8 text-orange-500" />
              Community
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Connect with your community and share updates
            </p>
          </div>
          <Button 
            onClick={() => window.location.href = '/territories?action=create-community'}
            className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700"
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            Create Community
          </Button>
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
                    <Label>Select Territory</Label>
                    <Select value={selectedTerritory} onValueChange={setSelectedTerritory}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose territory" />
                      </SelectTrigger>
                      <SelectContent>
                        {territories.map(territory => (
                          <SelectItem key={territory.id} value={territory.id}>
                            {territory.name} ({territory.zone})
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
      </div>
    </div>
  );
};
