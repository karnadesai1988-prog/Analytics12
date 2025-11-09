import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Zap, Mail, Lock, User, Sparkles } from 'lucide-react';

export const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', name: '', role: 'viewer' });
  const [loading, setLoading] = useState(false);
  const { login, signup } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await signup(formData.name, formData.email, formData.password, formData.role);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 left-20 w-72 h-72 bg-blue-200/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-100/40 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-50/30 rounded-full blur-3xl" />
      </div>

      <Card className="w-full max-w-md glass-panel-light border shadow-2xl relative z-10" style={{borderColor: '#E0E0E0', boxShadow: '0 20px 60px rgba(0, 0, 0, 0.12)'}}>
        <CardHeader className="space-y-4 text-center">
          <div className="flex justify-center">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg float-animation" style={{boxShadow: '0 8px 24px rgba(37, 99, 235, 0.35)'}}>
              <Zap className="w-12 h-12 text-white" />
            </div>
          </div>
          <div>
            <CardTitle className="text-3xl font-bold mb-2" style={{color: '#1A1A1A'}}>
              {isLogin ? 'Welcome Back' : 'Join Us'}
            </CardTitle>
            <CardDescription className="text-base" style={{color: '#4F4F4F'}}>
              {isLogin ? 'Sign in to access your territory insights' : 'Create an account to get started'}
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div className="space-y-2">
                <Label className="flex items-center gap-2" style={{color: '#4F4F4F'}}>
                  <User className="w-4 h-4 text-blue-500" />
                  Full Name
                </Label>
                <Input
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-glass"
                  required={!isLogin}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label className="flex items-center gap-2" style={{color: '#4F4F4F'}}>
                <Mail className="w-4 h-4 text-blue-500" />
                Email Address
              </Label>
              <Input
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="input-glass"
                required
              />
            </div>

            <div className="space-y-2">
              <Label className="flex items-center gap-2" style={{color: '#4F4F4F'}}>
                <Lock className="w-4 h-4 text-orange-500" />
                Password
              </Label>
              <Input
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="input-glass"
                required
              />
            </div>

            {!isLogin && (
              <div className="space-y-2">
                <Label className="flex items-center gap-2" style={{color: '#4F4F4F'}}>
                  <Sparkles className="w-4 h-4 text-orange-500" />
                  Role
                </Label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="input-glass w-full"
                >
                  <option value="viewer">Viewer</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="community_head">Community Head</option>
                </select>
              </div>
            )}

            <Button
              type="submit"
              disabled={loading}
              className="w-full btn-orange-gradient py-6 text-base font-semibold rounded-xl"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>{isLogin ? 'Signing In...' : 'Creating Account...'}</span>
                </div>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </Button>
          </form>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm transition-colors duration-300" style={{color: '#8C8C8C'}}
            >
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <span className="text-orange-500 font-semibold underline hover:text-orange-600">
                {isLogin ? 'Sign Up' : 'Sign In'}
              </span>
            </button>
          </div>

          {/* Demo Credentials */}
          <div className="glass-panel p-4 rounded-xl border" style={{borderColor: '#E0E0E0'}}>
            <p className="text-xs font-semibold mb-2" style={{color: '#4F4F4F'}}>Demo Credentials:</p>
            <div className="space-y-1 text-xs" style={{color: '#8C8C8C'}}>
              <p>Admin: <span className="text-orange-500 font-medium">admin@test.com</span> / <span className="text-orange-500 font-medium">password123</span></p>
              <p>Viewer: <span className="text-orange-500 font-medium">viewer@test.com</span> / <span className="text-orange-500 font-medium">password123</span></p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};