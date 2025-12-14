import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Users,
  UserPlus,
  Shield,
  Mail,
  Phone,
  Calendar,
  Edit,
  Trash2,
  LogOut,
  Home,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/lib/supabase';

interface AdminUser {
  id: string;
  email: string;
  phone: string;
  name: string;
  role: 'super_admin' | 'admin' | 'manager';
  created_at: string;
  last_login?: string;
  status: 'active' | 'inactive';
}

export default function UserManagement() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [hasUsers, setHasUsers] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    name: '',
    role: 'admin' as AdminUser['role']
  });

  // Check authentication and load users
  useEffect(() => {
    checkAuthAndLoadUsers();
  }, []);

  const checkAuthAndLoadUsers = async () => {
    setLoading(true);
    try {
      // Check if any users exist
      const { data: existingUsers, error: countError } = await supabase
        .from('admin_users')
        .select('id')
        .limit(1);

      if (countError) {
        console.error('Error checking users:', countError);
      }

      const usersExist = existingUsers && existingUsers.length > 0;
      setHasUsers(usersExist);

      // Check if authenticated
      const authenticated = sessionStorage.getItem('adminAuthenticated') === 'true';
      setIsAuthenticated(authenticated);

      // If users exist AND not authenticated, redirect to login
      if (usersExist && !authenticated) {
        toast({
          title: 'Authentication Required',
          description: 'Please log in to manage users.',
          variant: 'destructive',
        });
        navigate('/admin/login');
        return;
      }

      // Load all users if authenticated or no users exist yet
      if (authenticated || !usersExist) {
        await loadUsers();
      }
    } catch (error) {
      console.error('Error in checkAuthAndLoadUsers:', error);
      toast({
        title: 'Error',
        description: 'Failed to load user data.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const { data, error } = await supabase
        .from('admin_users')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;

      setUsers(data || []);
    } catch (error) {
      console.error('Error loading users:', error);
      toast({
        title: 'Error',
        description: 'Failed to load users.',
        variant: 'destructive',
      });
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Validate form
      if (!formData.email || !formData.name) {
        toast({
          title: 'Validation Error',
          description: 'Email and name are required.',
          variant: 'destructive',
        });
        return;
      }

      // Create user
      const { data, error } = await supabase
        .from('admin_users')
        .insert([
          {
            email: formData.email,
            phone: formData.phone,
            name: formData.name,
            role: formData.role,
            status: 'active'
          }
        ])
        .select();

      if (error) throw error;

      toast({
        title: 'Success',
        description: `User ${formData.name} created successfully!`,
      });

      // Reset form
      setFormData({
        email: '',
        phone: '',
        name: '',
        role: 'admin'
      });

      // Close dialog and reload users
      setCreateDialogOpen(false);
      await loadUsers();

      // If this was the first user, update hasUsers state
      if (!hasUsers) {
        setHasUsers(true);
        toast({
          title: 'First Admin Created!',
          description: 'You can now log in with this admin account.',
        });
      }
    } catch (error) {
      console.error('Error creating user:', error);
      toast({
        title: 'Error',
        description: 'Failed to create user. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteUser = async (userId: string, userName: string) => {
    if (!confirm(`Are you sure you want to delete ${userName}?`)) {
      return;
    }

    try {
      const { error } = await supabase
        .from('admin_users')
        .delete()
        .eq('id', userId);

      if (error) throw error;

      toast({
        title: 'Success',
        description: `User ${userName} deleted successfully.`,
      });

      await loadUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete user.',
        variant: 'destructive',
      });
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('adminAuthenticated');
    sessionStorage.removeItem('adminLoginTime');
    sessionStorage.removeItem('adminUserId');
    sessionStorage.removeItem('adminUserEmail');
    sessionStorage.removeItem('adminUserName');
    sessionStorage.removeItem('adminUserRole');
    navigate('/admin/login');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#f8f9fa' }}>
      {/* Header */}
      <div
        className="shadow-lg"
        style={{
          background: 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Users className="w-8 h-8" style={{ color: '#d4af37' }} />
              <div>
                <h1 className="text-xl font-medium text-white">User Management</h1>
                <p className="text-xs" style={{ color: '#95a5a6' }}>
                  Manage admin users and permissions
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button
                onClick={() => navigate('/admin/dashboard')}
                variant="ghost"
                className="text-white hover:bg-white/10"
              >
                <Home className="w-4 h-4 mr-2" />
                Dashboard
              </Button>
              {isAuthenticated && (
                <Button
                  onClick={handleLogout}
                  variant="ghost"
                  className="text-white hover:bg-white/10"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* No Users - First Admin Setup */}
        {!hasUsers && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <AlertCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-blue-900 mb-2">
                      Welcome to ConcordBroker Admin
                    </h3>
                    <p className="text-sm text-blue-700 mb-4">
                      No admin users exist yet. Create the first admin user to get started.
                      This is a one-time setup that doesn't require authentication.
                    </p>
                    <p className="text-xs text-blue-600">
                      After creating the first admin, you'll need to log in to manage additional users.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Create User Button/Dialog */}
        <div className="mb-6">
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <UserPlus className="w-4 h-4 mr-2" />
                {hasUsers ? 'Create New User' : 'Create First Admin User'}
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>
                  {hasUsers ? 'Create New Admin User' : 'Create First Admin User'}
                </DialogTitle>
                <DialogDescription>
                  {hasUsers
                    ? 'Add a new administrator to the system.'
                    : 'This will be the primary administrator account.'}
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateUser} className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name *</Label>
                  <Input
                    id="name"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="admin@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="+1 (555) 123-4567"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select
                    value={formData.role}
                    onValueChange={(value: AdminUser['role']) =>
                      setFormData({ ...formData, role: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="super_admin">Super Admin</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="manager">Manager</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                    {hasUsers ? 'Create User' : 'Create Admin'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Users List */}
        <Card className="elegant-card">
          <CardHeader className="elegant-card-header">
            <CardTitle className="elegant-card-title gold-accent flex items-center">
              <Users className="w-5 h-5 mr-2" style={{ color: '#d4af37' }} />
              All Users
            </CardTitle>
            <CardDescription>
              {users.length === 0
                ? 'No users found. Create the first admin user to get started.'
                : `Managing ${users.length} admin user${users.length !== 1 ? 's' : ''}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 mb-4">No users found</p>
                <p className="text-sm text-gray-400">
                  Click the button above to create your first admin user
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {users.map((user, index) => (
                  <motion.div
                    key={user.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                    style={{ borderColor: '#ecf0f1' }}
                  >
                    <div className="flex items-start space-x-4 flex-1">
                      <div
                        className="p-3 rounded-full"
                        style={{
                          backgroundColor:
                            user.role === 'super_admin'
                              ? 'rgba(231, 76, 60, 0.1)'
                              : user.role === 'admin'
                              ? 'rgba(52, 152, 219, 0.1)'
                              : 'rgba(149, 165, 166, 0.1)',
                        }}
                      >
                        <Shield
                          className="w-5 h-5"
                          style={{
                            color:
                              user.role === 'super_admin'
                                ? '#e74c3c'
                                : user.role === 'admin'
                                ? '#3498db'
                                : '#95a5a6',
                          }}
                        />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium" style={{ color: '#2c3e50' }}>
                          {user.name}
                        </h3>
                        <div className="flex items-center space-x-4 mt-2 text-sm" style={{ color: '#7f8c8d' }}>
                          <div className="flex items-center">
                            <Mail className="w-3 h-3 mr-1" />
                            {user.email}
                          </div>
                          {user.phone && (
                            <div className="flex items-center">
                              <Phone className="w-3 h-3 mr-1" />
                              {user.phone}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-4 mt-1 text-xs" style={{ color: '#95a5a6' }}>
                          <div className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            Joined {new Date(user.created_at).toLocaleDateString()}
                          </div>
                          <div className="px-2 py-1 rounded-full text-xs font-medium" style={{
                            backgroundColor: user.status === 'active' ? '#d4edda' : '#f8d7da',
                            color: user.status === 'active' ? '#155724' : '#721c24'
                          }}>
                            {user.status}
                          </div>
                          <div className="px-2 py-1 rounded-full text-xs font-medium" style={{
                            backgroundColor: user.role === 'super_admin' ? '#f8d7da' : user.role === 'admin' ? '#d1ecf1' : '#e2e3e5',
                            color: user.role === 'super_admin' ? '#721c24' : user.role === 'admin' ? '#0c5460' : '#383d41'
                          }}>
                            {user.role.replace('_', ' ')}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="hover:bg-blue-50"
                        onClick={() => {
                          toast({
                            title: 'Edit User',
                            description: 'Edit functionality coming soon!',
                          });
                        }}
                      >
                        <Edit className="w-4 h-4 text-blue-600" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="hover:bg-red-50"
                        onClick={() => handleDeleteUser(user.id, user.name)}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
