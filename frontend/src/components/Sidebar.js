import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Button } from './ui/button';
import { cn } from '../lib/utils';
import { MapPin, LayoutDashboard, FileText, MessageSquare, LogOut, Wifi, WifiOff, Settings } from 'lucide-react';

const navigation = [
  { name: 'Territories & Map', href: '/territories', icon: MapPin },
  { name: 'Dashboard & Analytics', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Feedback & Suggestions', href: '/data-gathering', icon: FileText },
  { name: 'Community Pulse', href: '/comments', icon: MessageSquare },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { connected } = useWebSocket();

  return (
    <div className="flex h-screen w-64 flex-col bg-card border-r border-border" data-testid="sidebar">
      <div className="flex h-16 items-center justify-between px-6 border-b border-border">
        <div className="flex items-center gap-2">
          <MapPin className="w-6 h-6 text-primary" />
          <span className="text-lg font-bold">R Territory</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-3">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link key={item.name} to={item.href} data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={cn('flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}>
                <item.icon className="w-5 h-5" />{item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-border p-4 space-y-3">
        <div className="flex items-center gap-2 px-3 py-2 bg-accent/50 rounded-lg">
          {connected ? (<><Wifi className="w-4 h-4 text-green-600" /><span className="text-xs font-medium">Synced</span></>) : (<><WifiOff className="w-4 h-4 text-destructive" /><span className="text-xs font-medium">Offline</span></>)}
        </div>
        <div className="px-3 py-2 bg-accent/50 rounded-lg"><p className="text-xs font-medium">{user?.name}</p><p className="text-xs text-muted-foreground capitalize">{user?.role?.replace('_', ' ')}</p></div>
        <Button onClick={logout} variant="outline" className="w-full justify-start" data-testid="logout-button"><LogOut className="w-4 h-4 mr-2" />Sign Out</Button>
      </div>
    </div>
  );
};