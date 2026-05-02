import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Toaster } from 'react-hot-toast';
import PrivateRoute from './components/PrivateRoute';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import DiseaseDetector from './pages/DiseaseDetector';
import FertilizerForm from './pages/FertilizerForm';
import PricePredictor from './pages/PricePredictor';
import VoiceAssistant from './pages/VoiceAssistant';

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <PrivateRoute>
          <Layout><Dashboard /></Layout>
        </PrivateRoute>
      } />
      <Route path="/disease" element={
        <PrivateRoute>
          <Layout><DiseaseDetector /></Layout>
        </PrivateRoute>
      } />
      <Route path="/fertilizer" element={
        <PrivateRoute>
          <Layout><FertilizerForm /></Layout>
        </PrivateRoute>
      } />
      <Route path="/price" element={
        <PrivateRoute>
          <Layout><PricePredictor /></Layout>
        </PrivateRoute>
      } />
      <Route path="/voice" element={
        <PrivateRoute>
          <Layout><VoiceAssistant /></Layout>
        </PrivateRoute>
      } />
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#232923',
              color: '#E8E8E8',
              border: '1px solid #3A423A',
              borderRadius: '12px',
              fontSize: '14px',
            },
            success: {
              iconTheme: { primary: '#52B788', secondary: '#fff' },
            },
            error: {
              iconTheme: { primary: '#E76F51', secondary: '#fff' },
            },
          }}
        />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
