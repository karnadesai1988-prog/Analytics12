import React, { useEffect, useState } from 'react';
import { territoryAPI, commentAPI } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { MessageSquare, Send, Shield, Bot } from 'lucide-react';
import { motion } from 'framer-motion';

export const Comments = () => {
  const [territories, setTerritories] = useState([]);
  const [selectedTerritory, setSelectedTerritory] = useState('');
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [useAI, setUseAI] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTerritories();
  }, []);

  useEffect(() => {
    if (selectedTerritory) {
      loadComments();
    }
  }, [selectedTerritory]);

  const loadTerritories = async () => {
    try {
      const response = await territoryAPI.getAll();
      setTerritories(response.data);
      if (response.data.length > 0) {
        setSelectedTerritory(response.data[0].id);
      }
    } catch (error) {
      toast.error('Failed to load territories');
    }
  };

  const loadComments = async () => {
    try {
      const response = await commentAPI.getByTerritory(selectedTerritory);
      setComments(response.data);
    } catch (error) {
      console.error('Failed to load comments:', error);
      setComments([]);
    }
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || !selectedTerritory) {
      toast.error('Please enter a comment');
      return;
    }

    setLoading(true);
    try {
      await commentAPI.create({
        territoryId: selectedTerritory,
        text: newComment,
        useAI: useAI
      });
      toast.success('Comment posted successfully!');
      setNewComment('');
      loadComments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to post comment');
    } finally {
      setLoading(false);
    }
  };

  const getValidationBadge = (status) => {
    if (status === 'valid') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
          <Shield className="w-3 h-3" />
          Verified
        </span>
      );
    } else if (status === 'flagged') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
          <Shield className="w-3 h-3" />
          Flagged
        </span>
      );
    }
    return null;
  };

  return (
    <div className="p-6 space-y-6" data-testid="comments-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Community Comments</h1>
          <p className="text-muted-foreground mt-1">AI-validated community feedback and discussions</p>
        </div>
        <div className="w-64">
          <Select value={selectedTerritory} onValueChange={setSelectedTerritory}>
            <SelectTrigger data-testid="comment-territory-select">
              <SelectValue placeholder="Select territory" />
            </SelectTrigger>
            <SelectContent>
              {territories.map((territory) => (
                <SelectItem key={territory.id} value={territory.id}>
                  {territory.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Post Comment */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-1"
        >
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Post Comment
              </CardTitle>
              <CardDescription>
                Share your feedback about this territory
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmitComment} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="comment">Your Comment</Label>
                  <textarea
                    id="comment"
                    data-testid="comment-input"
                    className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Share your thoughts..."
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-accent/50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4 text-primary" />
                    <Label htmlFor="useAI" className="text-sm cursor-pointer">
                      AI Validation
                    </Label>
                  </div>
                  <Switch
                    id="useAI"
                    data-testid="ai-validation-toggle"
                    checked={useAI}
                    onCheckedChange={setUseAI}
                  />
                </div>

                <p className="text-xs text-muted-foreground">
                  {useAI
                    ? 'AI will analyze your comment for inappropriate content using GPT-5'
                    : 'Basic regex validation will be applied'}
                </p>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={loading}
                  data-testid="submit-comment-button"
                >
                  <Send className="w-4 h-4 mr-2" />
                  {loading ? 'Posting...' : 'Post Comment'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </motion.div>

        {/* Comments List */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle>Comments Feed</CardTitle>
              <CardDescription>
                {comments.length} comment{comments.length !== 1 ? 's' : ''} on this territory
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {comments.length > 0 ? (
                  comments.map((comment) => (
                    <div key={comment.id} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">{comment.userName}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(comment.createdAt).toLocaleString()}
                          </p>
                        </div>
                        {getValidationBadge(comment.validationStatus)}
                      </div>
                      <p className="text-sm">{comment.text}</p>
                      {comment.validationReason && (
                        <div className="flex items-start gap-2 p-2 bg-accent/30 rounded text-xs">
                          <Shield className="w-3 h-3 mt-0.5 text-muted-foreground" />
                          <span className="text-muted-foreground">{comment.validationReason}</span>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No comments yet. Be the first to share your thoughts!</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};