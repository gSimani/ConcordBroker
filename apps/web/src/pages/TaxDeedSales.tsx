import React, { useState } from 'react'
import Layout from '@/components/layout'
import { TaxDeedSalesTab } from '@/components/property/tabs/TaxDeedSalesTab'
import { Gavel, Filter, TrendingUp, Home, Building2, DollarSign, AlertCircle, Calendar, Phone } from 'lucide-react'
import { motion } from 'framer-motion'

export default function TaxDeedSales() {
  const [activeView, setActiveView] = useState<'grid' | 'list'>('list')

  return (
    <Layout>
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-navy via-blue-900 to-navy overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-50"></div>
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 w-96 h-96 bg-gold opacity-10 rounded-full blur-3xl transform -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-400 opacity-10 rounded-full blur-3xl transform translate-x-1/2 translate-y-1/2"></div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-gold bg-opacity-20 rounded-full">
                <Gavel className="w-12 h-12 text-gold" />
              </div>
            </div>
            <h1 className="text-5xl font-light text-white mb-4">
              Tax Deed <span className="text-gold font-semibold">Sales</span>
            </h1>
            <p className="text-xl text-gray-200 max-w-3xl mx-auto">
              Monitor upcoming tax deed auctions, track properties, and manage owner outreach all in one place
            </p>
          </motion.div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Page Header with Actions */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-light text-navy">
                Active <span className="font-semibold">Opportunities</span>
              </h2>
              <p className="text-gray-600 mt-2">
                Track and manage tax deed properties with integrated contact management
              </p>
            </div>
            <div className="flex gap-3">
              <button className="px-6 py-3 bg-white border border-gray-300 text-navy rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2">
                <Filter className="w-4 h-4" />
                Export Data
              </button>
              <button className="px-6 py-3 bg-gold text-white rounded-lg hover:bg-gold-dark transition-colors flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Analytics
              </button>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"
        >
          <div className="bg-gradient-to-br from-blue-50 to-white p-6 rounded-lg border border-blue-100">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Building2 className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-navy mb-2">Sunbiz Integration</h3>
                <p className="text-sm text-gray-600">
                  Automatic entity matching with direct links to Sunbiz records for applicant research
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-50 to-white p-6 rounded-lg border border-green-100">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Home className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-navy mb-2">Property Links</h3>
                <p className="text-sm text-gray-600">
                  Direct access to Property Appraiser records and GIS maps for detailed research
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-lg border border-purple-100">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Phone className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-navy mb-2">Contact Management</h3>
                <p className="text-sm text-gray-600">
                  Track outreach efforts with phone, email, notes, and status tracking
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Tax Deed Sales Component */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <TaxDeedSalesTab />
        </motion.div>
      </div>
    </Layout>
  )
}