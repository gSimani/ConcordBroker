import React, { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ScraperControls from '@/components/admin/ScraperControls';

export default function ScrapersPage() {
  const navigate = useNavigate();

  // Check authentication
  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('adminAuthenticated');
    if (!isAuthenticated) {
      navigate('/Gate14');
    }
  }, [navigate]);

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
                <h1 className="text-xl font-medium text-white">Data Scraper Management</h1>
                <p className="text-xs" style={{ color: '#95a5a6' }}>
                  Manual control for automated data extraction workflows
                </p>
              </div>
            </div>

            <Button
              onClick={() => navigate('/admin/dashboard')}
              variant="ghost"
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Admin
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ScraperControls />
      </div>
    </div>
  );
}
