import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { canAccessRoute, normalizeRole } from '../utils/roles';
import type { Role } from '../types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: Role[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isVerifying } = useAuth();
  const location = useLocation();
  const role = user?.role;
  const normalizedRole = role ? normalizeRole(role) : null;
  const pathname = location.pathname;

  // While verifying session, show a loading spinner (don't redirect yet)
  if (isVerifying) {
    console.log(`[ProtectedRoute] user=${user?.email ?? 'null'}, role=${normalizedRole ?? 'null'}, pathname=${pathname}, access=verifying`);
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--bg-base)]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-secondary/30 border-t-secondary rounded-full animate-spin" />
          <span className="text-sm text-on-surface-variant">Verifying session…</span>
        </div>
      </div>
    );
  }

  if (!user) {
    console.log(`[ProtectedRoute] user=null, role=null, pathname=${pathname}, access=denied`);
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && normalizedRole) {
    const normalizedAllowed = allowedRoles.map(r => normalizeRole(r));
    if (!normalizedAllowed.includes(normalizedRole)) {
      console.warn(`[ProtectedRoute] user=${user.email}, role=${normalizedRole} (raw: ${role}), pathname=${pathname}, access=denied`);
      return <Navigate to="/" replace />;
    }
  }

  if (normalizedRole && !canAccessRoute(normalizedRole, pathname)) {
    console.warn(`[ProtectedRoute] user=${user.email}, role=${normalizedRole}, pathname=${pathname}, access=denied`);
    return <Navigate to="/" replace />;
  }

  console.log(`[ProtectedRoute] user=${user.email}, role=${normalizedRole}, pathname=${pathname}, access=allowed`);
  return <>{children}</>;
}
