import { api } from './client';
import type { User, Role } from '../types';

export interface UserCreateData {
  email: string;
  name: string;
  password?: string;
  role: Role;
  status?: 'ACTIVE' | 'INACTIVE';
}

export interface UserUpdateData {
  name?: string;
  role?: Role;
  status?: 'ACTIVE' | 'INACTIVE';
}

const normalizeUser = (u: any): User => ({
  ...u,
  role: u.role.toLowerCase().replace('_', '') as Role
});

export const adminApi = {
  getUsers: async (page = 1, limit = 50) => {
    console.log(`[adminApi] Fetching users: page=${page}, limit=${limit}`);
    const response = await api.get<any>(`/api/admin/users?page=${page}&limit=${limit}`);

    // Defensive normalization: backend might return [users] or { data: [users] }
    const rawUsers = Array.isArray(response) 
      ? response 
      : (response.data || response.items || []);

    console.log(`[adminApi] Received ${rawUsers.length} raw users`);
    return rawUsers.map(normalizeUser);
  },

  createUser: async (data: UserCreateData) => {
    // Restore underscore for backend enum if it's superadmin
    let backendRole = data.role.toUpperCase();
    if (backendRole === 'SUPERADMIN') backendRole = 'SUPER_ADMIN';

    const payload = { ...data, role: backendRole };
    const response = await api.post<any>('/api/admin/users', payload);
    return normalizeUser(response);
  },

  updateUser: async (userId: string, data: UserUpdateData) => {
    const payload = { ...data };
    if (payload.role) {
      let backendRole = payload.role.toUpperCase();
      if (backendRole === 'SUPERADMIN') backendRole = 'SUPER_ADMIN';
      payload.role = backendRole as Role;
    }
    const response = await api.patch<any>(`/api/admin/users/${userId}`, payload);
    return normalizeUser(response);
  },

  deleteUser: async (userId: string) => {
    await api.delete(`/api/admin/users/${userId}`);
  },

  resetPassword: async (userId: string, newPassword: string) => {
    await api.post(`/api/admin/users/${userId}/reset-password`, { new_password: newPassword });
  }
};

