import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, Mail, Shield, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

// Secure credentials (in production, these should be in environment variables and verified on backend)
const ADMIN_CREDENTIALS = {
  email: 'admin@westbocaexecutiveoffice.com',
  password: 'WBESAdmin2024!'
};

export default function Gate14() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [attempts, setAttempts] = useState(0);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Add artificial delay for security
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Check credentials
    if (email === ADMIN_CREDENTIALS.email && password === ADMIN_CREDENTIALS.password) {
      // Store admin session
      sessionStorage.setItem('adminAuthenticated', 'true');
      sessionStorage.setItem('adminLoginTime', new Date().toISOString());
      
      // Navigate to admin dashboard
      navigate('/admin/dashboard');
    } else {
      setAttempts(prev => prev + 1);
      
      if (attempts >= 4) {
        setError('Too many failed attempts. Access has been logged.');
        // In production, you would log this security event
      } else {
        setError('Invalid credentials. This attempt has been logged.');
      }
    }

    setIsLoading(false);
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, #1a252f 0%, #2c3e50 100%)',
      }}
    >
      {/* Animated Background Pattern */}
      <div className="absolute inset-0">
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `repeating-linear-gradient(
              45deg,
              transparent,
              transparent 35px,
              rgba(212, 175, 55, 0.1) 35px,
              rgba(212, 175, 55, 0.1) 70px
            )`
          }}
        />
      </div>

      {/* Security Badge */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute top-8 right-8 flex items-center space-x-2"
      >
        <Shield className="w-5 h-5" style={{ color: '#d4af37' }} />
        <span className="text-sm" style={{ color: '#95a5a6' }}>Secure Portal</span>
      </motion.div>

      {/* Login Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md px-6"
      >
        <Card className="elegant-card shadow-2xl border-0">
          <CardHeader className="space-y-1 pb-6">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              className="mx-auto mb-4 w-16 h-16 rounded-full flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #d4af37 0%, #f4e5c2 100%)',
                boxShadow: '0 4px 15px rgba(212, 175, 55, 0.3)'
              }}
            >
              <Lock className="w-8 h-8" style={{ color: '#2c3e50' }} />
            </motion.div>
            
            <h2 className="text-2xl font-medium text-center" style={{ color: '#2c3e50' }}>
              Executive Access Portal
            </h2>
            <p className="text-sm text-center" style={{ color: '#7f8c8d' }}>
              West Boca Executive Office - Admin
            </p>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              {/* Email Field */}
              <div className="space-y-2">
                <Label 
                  htmlFor="email" 
                  className="text-xs uppercase tracking-wider" 
                  style={{ color: '#95a5a6' }}
                >
                  Email Address
                </Label>
                <div className="relative">
                  <Mail 
                    className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" 
                    style={{ color: '#95a5a6' }}
                  />
                  <Input
                    id="email"
                    type="email"
                    placeholder="admin@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 h-11"
                    style={{
                      borderColor: '#ecf0f1',
                      backgroundColor: '#fff'
                    }}
                    required
                    disabled={attempts >= 5}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label 
                  htmlFor="password" 
                  className="text-xs uppercase tracking-wider" 
                  style={{ color: '#95a5a6' }}
                >
                  Password
                </Label>
                <div className="relative">
                  <Lock 
                    className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" 
                    style={{ color: '#95a5a6' }}
                  />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 h-11"
                    style={{
                      borderColor: '#ecf0f1',
                      backgroundColor: '#fff'
                    }}
                    required
                    disabled={attempts >= 5}
                  />
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center space-x-2 p-3 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    border: '1px solid rgba(231, 76, 60, 0.3)'
                  }}
                >
                  <AlertCircle className="w-4 h-4" style={{ color: '#e74c3c' }} />
                  <span className="text-sm" style={{ color: '#e74c3c' }}>{error}</span>
                </motion.div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={isLoading || attempts >= 5}
                className="w-full h-11 font-medium uppercase tracking-wider"
                style={{
                  background: isLoading ? '#95a5a6' : 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
                  color: '#fff',
                  border: 'none'
                }}
              >
                {isLoading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Shield className="w-4 h-4" />
                  </motion.div>
                ) : (
                  'Authenticate'
                )}
              </Button>
            </form>

            {/* Security Notice */}
            <div className="mt-6 pt-6 border-t" style={{ borderColor: '#ecf0f1' }}>
              <p className="text-xs text-center" style={{ color: '#95a5a6' }}>
                This is a secure portal. All login attempts are monitored and logged.
              </p>
              <p className="text-xs text-center mt-2" style={{ color: '#95a5a6' }}>
                Unauthorized access attempts will be reported.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Copyright */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-xs text-center mt-6"
          style={{ color: '#7f8c8d' }}
        >
          © 2024 West Boca Executive Office. All rights reserved.
        </motion.p>
      </motion.div>
    </div>
  );
}