import React, { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Users, 
  Building, 
  Truck,
  FileText,
  Settings,
  LogOut,
  Home,
  BarChart3,
  DollarSign,
  Activity
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function AdminDashboard() {
  const navigate = useNavigate();

  // Check authentication
  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('adminAuthenticated');
    if (!isAuthenticated) {
      navigate('/Gate14');
    }
  }, [navigate]);

  const handleLogout = () => {
    sessionStorage.removeItem('adminAuthenticated');
    sessionStorage.removeItem('adminLoginTime');
    navigate('/Gate14');
  };

  const adminCards = [
    {
      title: 'Properties',
      description: 'Manage all properties',
      icon: Building,
      href: '/admin/properties',
      color: '#2c3e50',
      bgColor: 'rgba(44, 62, 80, 0.1)'
    },
    {
      title: 'Users',
      description: 'User management',
      icon: Users,
      href: '/admin/users',
      color: '#27ae60',
      bgColor: 'rgba(39, 174, 96, 0.1)'
    },
    {
      title: 'Vendors',
      description: 'Manage vendors',
      icon: Truck,
      href: '/admin/vendors',
      color: '#e74c3c',
      bgColor: 'rgba(231, 76, 60, 0.1)'
    },
    {
      title: 'Reports',
      description: 'View analytics',
      icon: FileText,
      href: '/admin/reports',
      color: '#3498db',
      bgColor: 'rgba(52, 152, 219, 0.1)'
    },
    {
      title: 'Financial',
      description: 'Financial overview',
      icon: DollarSign,
      href: '/admin/financial',
      color: '#d4af37',
      bgColor: 'rgba(212, 175, 55, 0.1)'
    },
    {
      title: 'Settings',
      description: 'System settings',
      icon: Settings,
      href: '/admin/settings',
      color: '#95a5a6',
      bgColor: 'rgba(149, 165, 166, 0.1)'
    }
  ];

  const stats = [
    { label: 'Total Properties', value: '156', change: '+12%', positive: true },
    { label: 'Active Users', value: '1,234', change: '+5%', positive: true },
    { label: 'Monthly Revenue', value: '$45,678', change: '+18%', positive: true },
    { label: 'Pending Tasks', value: '23', change: '-8%', positive: false }
  ];

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
              <Shield className="w-8 h-8" style={{ color: '#d4af37' }} />
              <div>
                <h1 className="text-xl font-medium text-white">Admin Dashboard</h1>
                <p className="text-xs" style={{ color: '#95a5a6' }}>
                  West Boca Executive Office
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button
                onClick={() => navigate('/dashboard')}
                variant="ghost"
                className="text-white hover:bg-white/10"
              >
                <Home className="w-4 h-4 mr-2" />
                Main Site
              </Button>
              <Button
                onClick={handleLogout}
                variant="ghost"
                className="text-white hover:bg-white/10"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="elegant-card hover-lift">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-wider" style={{ color: '#95a5a6' }}>
                        {stat.label}
                      </p>
                      <p className="text-2xl font-medium mt-1" style={{ color: '#2c3e50' }}>
                        {stat.value}
                      </p>
                    </div>
                    <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      stat.positive ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                    }`}>
                      {stat.change}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Admin Actions Grid */}
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4" style={{ color: '#2c3e50' }}>
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {adminCards.map((card, index) => {
              const Icon = card.icon;
              return (
                <motion.div
                  key={card.title}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link to={card.href}>
                    <Card className="elegant-card hover-lift cursor-pointer group">
                      <CardContent className="p-6">
                        <div className="flex items-start space-x-4">
                          <div 
                            className="p-3 rounded-lg"
                            style={{ backgroundColor: card.bgColor }}
                          >
                            <Icon className="w-6 h-6" style={{ color: card.color }} />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium text-lg" style={{ color: '#2c3e50' }}>
                              {card.title}
                            </h3>
                            <p className="text-sm mt-1" style={{ color: '#7f8c8d' }}>
                              {card.description}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <Card className="elegant-card">
          <CardHeader className="elegant-card-header">
            <CardTitle className="elegant-card-title gold-accent flex items-center">
              <Activity className="w-5 h-5 mr-2" style={{ color: '#d4af37' }} />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { action: 'New property added', time: '2 minutes ago', user: 'System' },
                { action: 'User registration approved', time: '15 minutes ago', user: 'Admin' },
                { action: 'Vendor invoice processed', time: '1 hour ago', user: 'Finance' },
                { action: 'Monthly report generated', time: '3 hours ago', user: 'System' },
              ].map((activity, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between py-3 border-b"
                  style={{ borderColor: '#ecf0f1' }}
                >
                  <div>
                    <p className="text-sm font-medium" style={{ color: '#2c3e50' }}>
                      {activity.action}
                    </p>
                    <p className="text-xs" style={{ color: '#95a5a6' }}>
                      by {activity.user}
                    </p>
                  </div>
                  <span className="text-xs" style={{ color: '#7f8c8d' }}>
                    {activity.time}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}