import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Camera, Save, Lock, Upload, User as UserIcon } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardTitle, Button, Badge, Input, LoadingState, ErrorState } from '../../components/ui';
import { settingsApi, type UserProfile } from './api';
import { ROLE_LABELS } from '../../utils/roles';
import type { Role } from '../../types';

const ROLE_BADGE_VARIANTS: Record<string, 'info' | 'warning' | 'success' | 'default'> = {
  SUPERADMIN: 'warning',
  ADMIN: 'info',
  HR: 'success',
  INTERVIEWER: 'default',
  CANDIDATE: 'default',
};

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Profile form state
  const [name, setName] = useState('');
  const [nameInitialized, setNameInitialized] = useState(false);

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordErrors, setPasswordErrors] = useState<{ new?: string; confirm?: string }>({});

  // Photo upload state
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Fetch profile
  const {
    data: profile,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['settings-profile'],
    queryFn: settingsApi.getProfile,
  });

  // Initialize form fields from fetched data
  if (profile && !nameInitialized) {
    setName(profile.name || '');
    setNameInitialized(true);
  }

  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: (data: { name: string }) => settingsApi.updateProfile(data),
    onSuccess: () => {
      setSuccessMsg('Profile updated successfully');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['settings-profile'] });
      // Also invalidate the auth context user data
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
    onError: (err: Error) => {
      setErrorMsg(err.message);
      setSuccessMsg(null);
    },
  });

  // Change password mutation
  const passwordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string; confirm_password: string }) =>
      settingsApi.changePassword(data),
    onSuccess: () => {
      setSuccessMsg('Password changed successfully');
      setErrorMsg(null);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordErrors({});
    },
    onError: (err: Error) => {
      setErrorMsg(err.message);
      setSuccessMsg(null);
    },
  });

  // Upload photo mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => settingsApi.uploadPhoto(file),
    onSuccess: () => {
      setUploadError(null);
      setSuccessMsg('Photo updated successfully');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['settings-profile'] });
    },
    onError: (err: Error) => {
      setUploadError(err.message);
      setSuccessMsg(null);
    },
  });

  const validatePasswordForm = (): boolean => {
    const errors: { new?: string; confirm?: string } = {};
    if (newPassword.length > 0 && newPassword.length < 8) {
      errors.new = 'Password must be at least 8 characters';
    }
    if (confirmPassword && newPassword !== confirmPassword) {
      errors.confirm = 'Passwords do not match';
    }
    setPasswordErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSaveProfile = () => {
    if (!name.trim()) {
      setErrorMsg('Name cannot be empty');
      setSuccessMsg(null);
      return;
    }
    updateMutation.mutate({ name: name.trim() });
  };

  const handleChangePassword = () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      setErrorMsg('All password fields are required');
      setSuccessMsg(null);
      return;
    }
    if (!validatePasswordForm()) return;
    passwordMutation.mutate({
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
  };

  const handlePhotoClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    const allowedTypes = ['image/jpeg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      setUploadError('Only .jpg and .png files are allowed');
      return;
    }

    // Validate size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      setUploadError('File must be less than 2MB');
      return;
    }

    setUploadError(null);
    uploadMutation.mutate(file);
  };

  // Clear status messages after 4 seconds
  const showSuccess = (msg: string | null) => {
    if (msg) {
      setTimeout(() => setSuccessMsg(null), 4000);
    }
    return msg;
  };

  if (isLoading) {
    return (
      <AppShell title="Settings">
        <LoadingState message="Loading profile..." />
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell title="Settings">
        <ErrorState message="Failed to load profile" onRetry={refetch} />
      </AppShell>
    );
  }

  const roleBadgeVariant = ROLE_BADGE_VARIANTS[profile?.role || ''] || 'default';

  return (
    <AppShell title="Settings">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Status messages */}
        {showSuccess(successMsg) && (
          <div className="px-4 py-3 rounded-md bg-success-container/20 text-success text-sm flex items-center gap-2">
            <span>✓</span> {successMsg}
          </div>
        )}
        {errorMsg && (
          <div className="px-4 py-3 rounded-md bg-danger-container/20 text-danger text-sm flex items-center gap-2">
            <span>✕</span> {errorMsg}
          </div>
        )}

        {/* Avatar Upload Section */}
        <Card>
          <CardTitle>Profile Photo</CardTitle>
          <div className="flex items-center gap-6 mt-2">
            <div className="relative">
              <button
                onClick={handlePhotoClick}
                className="w-20 h-20 rounded-full bg-[var(--bg-layer1)] flex items-center justify-center overflow-hidden border-2 border-[var(--border-ghost)] hover:border-secondary/50 transition-colors group cursor-pointer"
                title="Click to upload photo"
              >
                {profile?.photo_url ? (
                  <img
                    src={profile.photo_url}
                    alt="Profile"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-2xl font-bold text-on-surface-variant">
                    {(profile?.name || 'U').charAt(0).toUpperCase()}
                  </span>
                )}
                <div className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <Camera size={20} className="text-white" />
                </div>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".jpg,.jpeg,.png"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-on-surface">Upload a photo</p>
              <p className="text-xs text-tertiary">JPG or PNG, max 2MB</p>
              {uploadMutation.isPending && (
                <p className="text-xs text-secondary">Uploading...</p>
              )}
              {uploadError && (
                <p className="text-xs text-danger">{uploadError}</p>
              )}
            </div>
          </div>
        </Card>

        {/* Profile Info Section */}
        <Card>
          <CardTitle>Profile Information</CardTitle>
          <div className="space-y-4 mt-2">
            <Input
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your full name"
            />
            <div>
              <label className="block text-sm font-medium text-on-tertiary-container mb-1.5">
                Email
              </label>
              <input
                value={profile?.email || ''}
                disabled
                className="w-full rounded-md bg-[var(--bg-layer2)] px-3 py-2 text-sm text-tertiary cursor-not-allowed ring-1 ring-[var(--border-ghost)] opacity-60"
              />
            </div>
            <div className="flex items-center gap-3">
              <div>
                <label className="block text-sm font-medium text-on-tertiary-container mb-1.5">
                  Role
                </label>
                <Badge variant={roleBadgeVariant}>
                  {ROLE_LABELS[(profile?.role?.toLowerCase() || 'candidate') as Role] || profile?.role || 'Candidate'}
                </Badge>
              </div>
              {profile?.created_at && (
                <div>
                  <label className="block text-sm font-medium text-on-tertiary-container mb-1.5">
                    Member since
                  </label>
                  <p className="text-sm text-tertiary">
                    {new Date(profile.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </p>
                </div>
              )}
            </div>
            <div className="pt-2">
              <Button
                variant="primary"
                size="md"
                onClick={handleSaveProfile}
                isLoading={updateMutation.isPending}
                disabled={!name.trim()}
              >
                <Save size={14} />
                Save Changes
              </Button>
            </div>
          </div>
        </Card>

        {/* Password Change Section */}
        <Card>
          <CardTitle>Change Password</CardTitle>
          <div className="space-y-4 mt-2">
            <Input
              label="Current Password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
            />
            <Input
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                if (passwordErrors.new) validatePasswordForm();
              }}
              placeholder="At least 8 characters"
              error={passwordErrors.new}
            />
            <Input
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (passwordErrors.confirm) validatePasswordForm();
              }}
              placeholder="Re-enter new password"
              error={passwordErrors.confirm}
            />
            <div className="pt-2">
              <Button
                variant="primary"
                size="md"
                onClick={handleChangePassword}
                isLoading={passwordMutation.isPending}
                disabled={!currentPassword || !newPassword || !confirmPassword}
              >
                <Lock size={14} />
                Update Password
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
