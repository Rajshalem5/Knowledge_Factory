import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { canAccessRoute, normalizeRole } from '../utils/roles';
import type { Role } from '../types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: Role[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user } = useAuth();
  const location = useLocation();
  const role = user?.role;
  const normalizedRole = role ? normalizeRole(role) : null;

  if (!user) {
    console.log(`[ProtectedRoute] No user, redirecting to /login. From: ${location.pathname}`);
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && normalizedRole) {
    const normalizedAllowed = allowedRoles.map(r => normalizeRole(r));
    if (!normalizedAllowed.includes(normalizedRole)) {
      console.warn(`[ProtectedRoute] Permission denied: Role=${normalizedRole} (raw: ${role}), Allowed=[${normalizedAllowed.join(', ')}] (raw: [${allowedRoles.join(', ')}]), Path=${location.pathname}. Redirecting to /`);
      return <Navigate to="/" replace />;
    }
  }

  if (normalizedRole && !canAccessRoute(normalizedRole, location.pathname)) {
    console.warn(`[ProtectedRoute] Route access denied: Role=${normalizedRole}, Path=${location.pathname}. Redirecting to /`);
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
