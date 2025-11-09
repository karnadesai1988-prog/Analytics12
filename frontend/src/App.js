import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { Toaster } from './components/ui/sonner';
import { Auth } from './components/Auth';
import { Sidebar } from './components/Sidebar';
import { DashboardNew } from './pages/DashboardNew';
import { TerritoriesUnified } from './pages/TerritoriesUnified';
import { DataSubmission } from './pages/DataSubmission';
import { Community } from './pages/Community';
import { TerritoryProfile } from './pages/TerritoryProfile';
import { Settings } from './pages/Settings';
import { News } from './pages/News';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="text-lg text-muted-foreground">Loading...</div></div>;
  return user ? children : <Navigate to="/" replace />;
};

const AppContent = () => {
  const { user } = useAuth();
  if (!user) return <Auth />;
  return (
    <div className="flex h-screen overflow-hidden" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
      <Sidebar />
      <main className="flex-1 overflow-y-auto" style={{background: 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F4 100%)'}}>
        <Routes>
          <Route path="/dashboard" element={<PrivateRoute><DashboardNew /></PrivateRoute>} />
          <Route path="/territories" element={<PrivateRoute><TerritoriesUnified /></PrivateRoute>} />
          <Route path="/territory/:territoryId" element={<PrivateRoute><TerritoryProfile /></PrivateRoute>} />
          <Route path="/data-gathering" element={<PrivateRoute><DataSubmission /></PrivateRoute>} />
          <Route path="/comments" element={<PrivateRoute><Community /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WebSocketProvider>
          <div className="App"><AppContent /><Toaster position="top-right" richColors /></div>
        </WebSocketProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;