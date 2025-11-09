import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Button } from './ui/button';
import { cn } from '../lib/utils';
import { MapPin, LayoutDashboard, FileText, MessageSquare, LogOut, Wifi, WifiOff, Settings, Zap } from 'lucide-react';

const navigation = [
  { name: 'Territories & Map', href: '/territories', icon: MapPin },
  { name: 'Dashboard & Analytics', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Feedback & Suggestions', href: '/data-gathering', icon: FileText },
  { name: 'Community', href: '/comments', icon: MessageSquare },
];

export const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { connected } = useWebSocket();

  return (
    <div className="flex h-screen w-64 flex-col glass-panel-dark border-r border-white/20" data-testid="sidebar" style={{background: 'rgba(10, 10, 10, 0.9)'}}>
      {/* Header */}
      <div className="flex h-20 items-center justify-between px-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 glow-orange">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold text-white">R Territory</span>
            <p className="text-xs text-gray-400">AI Insights</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-6">
        <nav className="space-y-2 px-4">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link 
                key={item.name} 
                to={item.href} 
                data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={cn(
                  'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300 group',
                  isActive 
                    ? 'bg-gradient-to-r from-orange-500 to-orange-600 text-white shadow-lg shadow-orange-500/50 transform scale-105' 
                    : 'text-gray-300 hover:bg-white/5 hover:text-white hover:shadow-lg hover:shadow-white/10'
                )}
              >
                <item.icon className={cn(
                  "w-5 h-5 transition-all duration-300",
                  isActive ? "text-white drop-shadow-lg" : "text-gray-400 group-hover:text-orange-400"
                )} />
                <span>{item.name}</span>
                {isActive && (
                  <div className="ml-auto w-2 h-2 rounded-full bg-white animate-pulse" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer */}
      <div className="border-t border-white/10 p-4 space-y-3">
        {/* Connection Status */}
        <div className={cn(
          "flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all duration-300",
          connected 
            ? "glass-panel border border-green-500/30 bg-green-500/10" 
            : "glass-panel border border-red-500/30 bg-red-500/10"
        )}>
          {connected ? (
            <>
              <Wifi className="w-4 h-4 text-green-400 animate-pulse" />
              <span className="text-xs font-medium text-green-300">Live Synced</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-400" />
              <span className="text-xs font-medium text-red-300">Offline</span>
            </>
          )}
        </div>

        {/* User Info */}
        <div className="glass-panel px-4 py-3 rounded-xl border border-white/20">
          <p className="text-sm font-semibold text-white">{user?.name}</p>
          <p className="text-xs text-gray-400 capitalize mt-0.5">
            {user?.role?.replace('_', ' ')}
          </p>
        </div>

        {/* Settings Button */}
        <Button 
          onClick={() => window.location.href = '/settings'} 
          className="w-full btn-glass justify-start hover:border-orange-500/50 rounded-xl"
        >
          <Settings className="w-4 h-4 mr-2" />
          <span>Settings</span>
        </Button>

        {/* Sign Out Button */}
        <Button 
          onClick={logout} 
          className="w-full btn-glass justify-start hover:border-red-500/50 hover:text-red-400 rounded-xl" 
          data-testid="logout-button"
        >
          <LogOut className="w-4 h-4 mr-2" />
          <span>Sign Out</span>
        </Button>
      </div>
    </div>
  );
};