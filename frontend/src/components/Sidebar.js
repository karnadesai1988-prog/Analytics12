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
  { name: 'Data Submission', href: '/data-submission', icon: FileText },
  { name: 'News', href: '/news', icon: FileText },
  { name: 'Community', href: '/comments', icon: MessageSquare },
];

export const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { connected } = useWebSocket();

  return (
    <div className="flex h-screen w-64 flex-col glass-panel-light border-r" data-testid="sidebar" style={{background: 'rgba(255, 255, 255, 0.75)', borderColor: '#E0E0E0'}}>
      {/* Header */}
      <div className="flex h-20 items-center justify-between px-6 border-b" style={{borderColor: '#E5E5E5'}}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg" style={{boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'}}>
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold" style={{color: '#1A1A1A'}}>R Territory</span>
            <p className="text-xs" style={{color: '#8C8C8C'}}>AI Insights</p>
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
                    ? 'bg-gradient-to-r from-orange-500 to-orange-600 text-white transform scale-105' 
                    : 'text-gray-700 hover:bg-white/60 hover:text-orange-600'
                )}
                style={isActive ? {boxShadow: '0 4px 12px rgba(255, 107, 0, 0.3)'} : {}}
              >
                <item.icon className={cn(
                  "w-5 h-5 transition-all duration-300",
                  isActive ? "text-white" : "text-gray-500 group-hover:text-orange-500"
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
      <div className="border-t p-4 space-y-3" style={{borderColor: '#E5E5E5'}}>
        {/* Connection Status */}
        <div className={cn(
          "flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all duration-300",
          connected 
            ? "glass-panel border border-green-400/40 bg-green-50/50" 
            : "glass-panel border border-red-400/40 bg-red-50/50"
        )}>
          {connected ? (
            <>
              <Wifi className="w-4 h-4 text-green-600 animate-pulse" />
              <span className="text-xs font-medium text-green-700">Live Synced</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-600" />
              <span className="text-xs font-medium text-red-700">Offline</span>
            </>
          )}
        </div>

        {/* User Info */}
        <div className="glass-panel px-4 py-3 rounded-xl border" style={{borderColor: '#E0E0E0'}}>
          <p className="text-sm font-semibold" style={{color: '#1A1A1A'}}>{user?.name}</p>
          <p className="text-xs capitalize mt-0.5" style={{color: '#8C8C8C'}}>
            {user?.role?.replace('_', ' ')}
          </p>
        </div>

        {/* Settings Button */}
        <Button 
          onClick={() => window.location.href = '/settings'} 
          className="w-full btn-glass justify-start rounded-xl"
        >
          <Settings className="w-4 h-4 mr-2" />
          <span>Settings</span>
        </Button>

        {/* Sign Out Button */}
        <Button 
          onClick={logout} 
          className="w-full btn-glass justify-start rounded-xl hover:border-red-400/50 hover:text-red-600" 
          data-testid="logout-button"
        >
          <LogOut className="w-4 h-4 mr-2" />
          <span>Sign Out</span>
        </Button>
      </div>
    </div>
  );
};