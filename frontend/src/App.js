import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { Toaster } from './components/ui/sonner';
import { Auth } from './components/Auth';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { TerritoriesNew } from './pages/TerritoriesNew';
import { DataGathering } from './pages/DataGathering';
import { Analytics } from './pages/Analytics';
import { Comments } from './pages/Comments';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return user ? children : <Navigate to="/" replace />;
};

const AppContent = () => {
  const { user } = useAuth();

  if (!user) {
    return <Auth />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/territories" element={<PrivateRoute><Territories /></PrivateRoute>} />
          <Route path="/data-gathering" element={<PrivateRoute><DataGathering /></PrivateRoute>} />
          <Route path="/analytics" element={<PrivateRoute><Analytics /></PrivateRoute>} />
          <Route path="/comments" element={<PrivateRoute><Comments /></PrivateRoute>} />
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
          <div className="App">
            <AppContent />
            <Toaster position="top-right" richColors />
          </div>
        </WebSocketProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;