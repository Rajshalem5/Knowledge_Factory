import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { getSafeHomeRoute } from './utils/roles';
import { ProtectedRoute } from './routes/ProtectedRoute';

console.log('[App.tsx] Initializing routing module...');

import Landing from './pages/Landing';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ClerkSignInPage from './pages/auth/ClerkSignInPage';
import AuthRedirect from './pages/auth/AuthRedirect';
import OTPVerification from './pages/auth/OTPVerification';
import ForgotPassword from './pages/auth/ForgotPassword';
import Portal from './pages/candidate/Portal';
import Assessment from './pages/candidate/Assessment';
import Dashboard from './pages/hr/Dashboard';
import CandidateDetail from './pages/hr/CandidateDetail';
import AssessmentReview from './pages/hr/AssessmentReview';
import ProctoringAudit from './pages/hr/ProctoringAudit';
import InterviewPanel from './pages/interviewer/InterviewPanel';
import SelectionPanel from './pages/selection/SelectionPanel';
import AnalyticsDashboard from './pages/analytics/AnalyticsDashboard';
import SuperAdminPanel from './pages/super_admin/SuperAdminPanel';
import CycleConfig from './pages/admin/CycleConfig';
import Privacy from './pages/legal/Privacy';
import Terms from './pages/legal/Terms';
import Settings from './pages/hr/Settings';
import AdminDashboard from './pages/admin/AdminDashboard';
import CookieConsent from './components/ui/CookieConsent';

import CandidatesList from './pages/hr/CandidatesList';
import UploadCenter from './pages/hr/UploadCenter';
import ResumeRepository from './pages/hr/ResumeRepository';

function AuthRedirectFallback() {
  const { user } = useAuth();
  const role = user?.role;
  if (!role) return <Navigate to="/login" replace />;
  const target = getSafeHomeRoute(role);
  console.log(`[AuthRedirect] UserRole=${role}, Redirecting to: ${target}`);
  return <Navigate to={target} replace />;
}

export default function App() {
  console.log('[App] Routes rendering');
  console.log('[App] Path:', window.location.pathname);
  return (
    <>
      <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Clerk auth routes — sign-in only, sign-up redirects to register */}
      <Route path="/sign-in/*" element={<ClerkSignInPage />} />
      <Route path="/sign-up" element={<Navigate to="/register" replace />} />
      <Route path="/sign-up/*" element={<Navigate to="/register" replace />} />
      <Route path="/redirect" element={<AuthRedirect />} />

      {/* Legacy auth routes */}
      <Route path="/verify-otp" element={<OTPVerification />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Candidate routes */}
      <Route path="/portal" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Portal />
        </ProtectedRoute>
      } />
      <Route path="/portal/assessments" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Portal tab="assessments" />
        </ProtectedRoute>
      } />
      <Route path="/portal/results" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Portal tab="results" />
        </ProtectedRoute>
      } />
      <Route path="/portal/documents" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Portal tab="documents" />
        </ProtectedRoute>
      } />
      <Route path="/portal/notifications" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Portal tab="notifications" />
        </ProtectedRoute>
      } />
      <Route path="/portal/profile" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Portal tab="profile" />
        </ProtectedRoute>
      } />
      <Route path="/assessment" element={
        <ProtectedRoute allowedRoles={['candidate']}>
          <Assessment />
        </ProtectedRoute>
      } />

      {/* HR / Admin / SuperAdmin routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <Dashboard />
        </ProtectedRoute>
      } />
      <Route path="/candidates" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <CandidatesList />
        </ProtectedRoute>
      } />
      <Route path="/uploads" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <UploadCenter />
        </ProtectedRoute>
      } />
      <Route path="/resumes" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <ResumeRepository />
        </ProtectedRoute>
      } />
      <Route path="/candidates/:id" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'interviewer', 'superadmin']}>
          <CandidateDetail />
        </ProtectedRoute>
      } />
      <Route path="/candidates/:id/assessments/:assessmentId" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'interviewer', 'superadmin']}>
          <AssessmentReview />
        </ProtectedRoute>
      } />
      <Route path="/candidates/:id/proctoring" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'interviewer', 'superadmin']}>
          <ProctoringAudit />
        </ProtectedRoute>
      } />

      {/* Interviewer routes */}
      <Route path="/interview" element={
        <ProtectedRoute allowedRoles={['interviewer', 'admin', 'superadmin']}>
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

      {/* Super Admin route */}
      <Route path="/admin/dashboard" element={
        <ProtectedRoute allowedRoles={['superadmin', 'admin']}>
          <SuperAdminPanel />
        </ProtectedRoute>
      } />
      <Route path="/admin/cycle-config" element={
        <ProtectedRoute allowedRoles={['superadmin', 'admin', 'hr']}>
          <CycleConfig />
        </ProtectedRoute>
      } />
      <Route path="/superadmin" element={
        <ProtectedRoute allowedRoles={['superadmin']}>
          <SuperAdminPanel />
        </ProtectedRoute>
      } />

      {/* Legal pages */}
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/terms" element={<Terms />} />

      {/* Settings */}
      <Route path="/settings" element={
        <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
          <Settings />
        </ProtectedRoute>
      } />

      {/* Admin Dashboard */}
      <Route path="/admin" element={
        <ProtectedRoute allowedRoles={['admin', 'superadmin']}>
          <AdminDashboard />
        </ProtectedRoute>
      } />

      {/* Fallback */}
      <Route path="*" element={<AuthRedirectFallback />} />
    </Routes>
    <CookieConsent />
    </>
  );
}
