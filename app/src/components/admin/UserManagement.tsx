import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi, type UserCreateData } from '../../api/admin';
import { Card, CardTitle, Badge, Button, Input, Select, Modal, LoadingState, ErrorState } from '../ui';
import { DataTable, type Column } from '../ui/DataTable';
import { useAuth } from '../../contexts/AuthContext';
import { ROLE_LABELS } from '../../utils/roles';
import { UserPlus, Trash2, Edit2, UserCheck, UserX } from 'lucide-react';
import type { User, Role } from '../../types';

interface UserManagementProps {
  manageAdmins?: boolean;
}

const ROLE_OPTIONS = [
  { value: 'hr', label: 'HR Recruiter' },
  { value: 'admin', label: 'Admin' },
  { value: 'interviewer', label: 'Interviewer' },
];

export function UserManagement({ manageAdmins = false }: UserManagementProps) {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  const [formData, setFormData] = useState<UserCreateData>({
    email: '',
    name: '',
    password: '',
    role: 'hr' as Role,
  });

  const { data: users, isLoading, error } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.getUsers(),
  });

  const createMutation = useMutation({
    mutationFn: (data: UserCreateData) => {
      console.log('[UserManagement] Creating user:', data);
      return adminApi.createUser(data);
    },
    onSuccess: () => {
      console.log('[UserManagement] User created successfully');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setIsCreateModalOpen(false);
      setFormData({ email: '', name: '', password: '', role: 'hr' as Role });
    },
    onError: (err: any) => {
      console.error('[UserManagement] User creation failed:', err);
      alert(`Failed to create user: ${err.message}`);
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string, data: any }) => {
      console.log(`[UserManagement] Updating user ${id}:`, data);
      return adminApi.updateUser(id, data);
    },
    onSuccess: () => {
      console.log('[UserManagement] User updated successfully');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setIsEditModalOpen(false);
    },
    onError: (err: any) => {
      console.error('[UserManagement] User update failed:', err);
      alert(`Failed to update user: ${err.message}`);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Failed to load users" />;

  // Normalize users data defensively
  const usersList = Array.isArray(users) 
    ? users 
    : (users as any)?.data || (users as any)?.items || [];

  // Filter users based on hierarchy
  const filteredUsers = usersList.filter((u: User) => {
    if (currentUser?.role === 'superadmin') {
      return true; // Super admin sees everyone
    }
    if (currentUser?.role === 'admin') {
      return u.role === 'hr' || u.role === 'interviewer'; // Admin only manages HR and Interviewers
    }
    return false;
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedUser) {
      updateMutation.mutate({ 
        id: selectedUser.id, 
        data: { name: formData.name, role: formData.role } 
      });
    }
  };

  const toggleUserStatus = (u: User) => {
    updateMutation.mutate({ 
      id: u.id, 
      data: { status: u.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE' } 
    });
  };

  const columns: Column<User>[] = [
    {
      key: 'name',
      header: 'User',
      render: (u) => (
        <div>
          <p className="text-sm font-medium text-on-surface">{u.name}</p>
          <p className="text-xs text-tertiary">{u.email}</p>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (u) => (
        <Badge variant={u.role === 'superadmin' ? 'warning' : u.role === 'admin' ? 'info' : 'success'}>
          {ROLE_LABELS[u.role] || u.role}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (u) => (
        <Badge variant={u.status === 'ACTIVE' ? 'success' : 'default'}>
          {u.status || 'ACTIVE'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (u) => (
        <div className="flex items-center gap-2">
          {u.role !== 'superadmin' && (
            <>
              <button 
                onClick={() => {
                  setSelectedUser(u);
                  setFormData({ email: u.email, name: u.name, role: u.role });
                  setIsEditModalOpen(true);
                }}
                className="p-1 hover:text-secondary transition-colors"
                title="Edit User"
              >
                <Edit2 size={14} />
              </button>
              <button 
                onClick={() => toggleUserStatus(u)}
                className={`p-1 transition-colors ${u.status === 'ACTIVE' ? 'hover:text-warning' : 'hover:text-success'}`}
                title={u.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
              >
                {u.status === 'ACTIVE' ? <UserX size={14} /> : <UserCheck size={14} />}
              </button>
              <button 
                onClick={() => { if(confirm('Delete user?')) deleteMutation.mutate(u.id); }}
                className="p-1 hover:text-danger transition-colors"
                title="Delete User"
              >
                <Trash2 size={14} />
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <CardTitle>User Management</CardTitle>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <UserPlus size={16} />
          Add User
        </Button>
      </div>

      <Card padding="none">
        <DataTable
          columns={columns}
          data={filteredUsers}
          keyExtractor={u => u.id}
        />
      </Card>

      {/* Create Modal */}
      <Modal 
        open={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New User"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <Input 
            label="Full Name" 
            required 
            value={formData.name} 
            onChange={e => setFormData({...formData, name: e.target.value})} 
          />
          <Input 
            label="Email" 
            type="email" 
            required 
            value={formData.email} 
            onChange={e => setFormData({...formData, email: e.target.value})} 
          />
          <Input 
            label="Initial Password" 
            type="password" 
            required 
            value={formData.password} 
            onChange={e => setFormData({...formData, password: e.target.value})} 
          />
          <Select 
            label="Role"
            options={currentUser?.role === 'superadmin' ? [
              ...ROLE_OPTIONS
            ] : [
              { value: 'hr', label: 'HR Recruiter' },
              { value: 'interviewer', label: 'Interviewer' },
            ]}
            value={formData.role}
            onChange={e => setFormData({...formData, role: e.target.value as Role})}
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal 
        open={isEditModalOpen} 
        onClose={() => setIsEditModalOpen(false)}
        title="Edit User"
      >
        <form onSubmit={handleUpdate} className="space-y-4">
          <Input 
            label="Full Name" 
            required 
            value={formData.name} 
            onChange={e => setFormData({...formData, name: e.target.value})} 
          />
          <Select 
            label="Role"
            options={currentUser?.role === 'superadmin' ? [
              ...ROLE_OPTIONS
            ] : [
              { value: 'hr', label: 'HR Recruiter' },
              { value: 'interviewer', label: 'Interviewer' },
            ]}
            value={formData.role}
            onChange={e => setFormData({...formData, role: e.target.value as Role})}
          />
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="secondary" onClick={() => setIsEditModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
