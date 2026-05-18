import { api } from '../../api/client';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: string;
  photo_url: string | null;
  status: string | null;
  created_at: string | null;
}

export const settingsApi = {
  getProfile: () => api.get<UserProfile>('/api/auth/me/profile'),
  updateProfile: (data: { name: string }) => api.patch<UserProfile>('/api/auth/me', data),
  changePassword: (data: { current_password: string; new_password: string; confirm_password: string }) =>
    api.post<{ message: string }>('/api/auth/change-password', data),
  uploadPhoto: (file: File) => {
    const formData = new FormData();
    formData.append('photo', file);
    return api.post<{ photo_url: string }>('/api/auth/upload-photo', formData);
  },
};
