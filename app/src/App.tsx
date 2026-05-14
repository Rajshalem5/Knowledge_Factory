import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { ROLE_HOME_ROUTES } from './utils/roles';
import { ProtectedRoute } from './routes/ProtectedRoute';

import Landing from './pages/Landing';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import OTPVerification from './pages/auth/OTPVerification';
import ForgotPassword from './pages/auth/ForgotPassword';
import Portal from './pages/candidate/Portal';
import Assessment from './pages/candidate/Assessment';
import Dashboard from './pages/hr/Dashboard';
import CandidateDetail from './pages/hr/CandidateDetail';
import InterviewPanel from './pages/interviewer/InterviewPanel';
import SelectionPanel from './pages/selection/SelectionPanel';
import AnalyticsDashboard from './pages/analytics/AnalyticsDashboard';
import SuperAdminPanel from './pages/superadmin/SuperAdminPanel';

function AuthRedirect() {
  const { user } = useAuth();
  const role = user?.role;
  if (!role) return <Navigate to="/login" replace />;
  return <Navigate to={ROLE_HOME_ROUTES[role]} replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-otp" element={<OTPVerification />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Candidate routes */}
      <Route path="/portal" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Portal />
        </ProtectedRoute>
      } />
      <Route path="/assessment" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Assessment />
        </ProtectedRoute>
      } />

      {/* HR / Admin routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <Dashboard />
        </ProtectedRoute>
      } />
      <Route path="/candidates" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'interviewer', 'superadmin']}>
          <Dashboard />
        </ProtectedRoute>
      } />
      <Route path="/candidates/:id" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'interviewer', 'superadmin']}>
          <CandidateDetail />
        </ProtectedRoute>
      } />

      {/* Interviewer routes */}
      <Route path="/interview" element={
        <ProtectedRoute allowedRoles={['interviewer', 'admin']}>
          <InterviewPanel />
        </ProtectedRoute>
      } />

      {/* Selection routes */}
      <Route path="/selection" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <SelectionPanel />
        </ProtectedRoute>
      } />

      {/* Analytics routes */}
      <Route path="/analytics" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <AnalyticsDashboard />
        </ProtectedRoute>
      } />

      {/* Super Admin routes */}
      <Route path="/superadmin" element={
        <ProtectedRoute allowedRoles={['superadmin']}>
          <SuperAdminPanel />
        </ProtectedRoute>
      } />

      {/* Fallback */}
      <Route path="*" element={<AuthRedirect />} />
    </Routes>
  );
}
