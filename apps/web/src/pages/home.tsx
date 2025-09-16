import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  Building2, 
  TrendingUp, 
  Shield, 
  Zap, 
  BarChart3, 
  Users,
  ArrowRight,
  Check,
  Star,
  Globe,
  Award,
  Clock
} from 'lucide-react'

export default function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-gray-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden px-6 pt-20 pb-32">
        {/* Animated Background */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
          <div className="absolute top-0 -right-4 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse" style={{ animationDelay: '2s' }}></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse" style={{ animationDelay: '4s' }}></div>
        </div>

        <div className="mx-auto max-w-7xl">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            {/* Badge */}
            <div className="inline-flex items-center px-4 py-2 mb-8 text-sm font-medium text-blue-700 bg-blue-100 rounded-full">
              <Zap className="w-4 h-4 mr-2" />
              New: AI-Powered Market Analysis
            </div>

            {/* Main Heading */}
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6">
              Real Estate Investment
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                Reimagined
              </span>
            </h1>

            {/* Subheading */}
            <p className="mx-auto max-w-2xl text-xl text-gray-600 mb-10">
              Access comprehensive property data, market trends, and investment insights 
              for Broward County. Make smarter real estate decisions with AI-powered analytics.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center px-8 py-4 text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl font-medium shadow-lg hover:shadow-xl transition-all"
              >
                Go to Dashboard
                <ArrowRight className="ml-2 w-5 h-5" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/properties')}
                className="inline-flex items-center px-8 py-4 text-gray-700 bg-white border-2 border-gray-200 rounded-xl font-medium shadow-lg hover:shadow-xl hover:border-gray-300 transition-all"
              >
                Search Properties
                <Building2 className="ml-2 w-5 h-5" />
              </motion.button>
            </div>

            {/* Trust Indicators */}
            <div className="mt-12 flex flex-wrap justify-center gap-8">
              <div className="flex items-center gap-2 text-gray-600">
                <Check className="w-5 h-5 text-green-500" />
                <span>50K+ Properties</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Check className="w-5 h-5 text-green-500" />
                <span>Real-time Data</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Check className="w-5 h-5 text-green-500" />
                <span>AI Analytics</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6 bg-white">
        <div className="mx-auto max-w-7xl">
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Succeed
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Powerful tools and insights designed for modern real estate professionals
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: BarChart3,
                title: "Advanced Analytics",
                description: "Deep market insights with AI-powered predictions and trend analysis",
                color: "blue"
              },
              {
                icon: Building2,
                title: "Property Database",
                description: "Access comprehensive data on thousands of properties in Broward County",
                color: "purple"
              },
              {
                icon: TrendingUp,
                title: "Portfolio Tracking",
                description: "Monitor your investments with real-time valuations and performance metrics",
                color: "green"
              },
              {
                icon: Shield,
                title: "Risk Assessment",
                description: "Evaluate investment risks with our proprietary scoring algorithms",
                color: "red"
              },
              {
                icon: Users,
                title: "Client Management",
                description: "Organize clients, track interactions, and manage your pipeline",
                color: "yellow"
              },
              {
                icon: Zap,
                title: "Instant Alerts",
                description: "Get notified about new opportunities and market changes in real-time",
                color: "indigo"
              }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -8, transition: { duration: 0.2 } }}
                className="p-8 bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-xl transition-all"
              >
                <div className="w-14 h-14 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl flex items-center justify-center mb-6">
                  <feature.icon className="w-7 h-7 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="mx-auto max-w-7xl">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            {[
              { value: "$2.5B+", label: "Properties Analyzed" },
              { value: "50K+", label: "Active Listings" },
              { value: "98%", label: "Data Accuracy" },
              { value: "24/7", label: "Real-time Updates" }
            ].map((stat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.5 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="text-4xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-blue-100">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 px-6 bg-gray-50">
        <div className="mx-auto max-w-7xl">
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Trusted by Industry Leaders
            </h2>
            <p className="text-xl text-gray-600">
              See what real estate professionals are saying
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: "Sarah Johnson",
                role: "Real Estate Broker",
                content: "ConcordBroker transformed how I analyze properties. The AI insights are game-changing.",
                rating: 5
              },
              {
                name: "Michael Chen",
                role: "Investment Manager",
                content: "The comprehensive data and analytics help me make confident investment decisions.",
                rating: 5
              },
              {
                name: "Emily Rodriguez",
                role: "Property Developer",
                content: "Best platform for market research. Saved me countless hours and improved my ROI.",
                rating: 5
              }
            ].map((testimonial, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                viewport={{ once: true }}
                className="p-8 bg-white rounded-2xl shadow-sm"
              >
                <div className="flex mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-gray-700 mb-6 italic">"{testimonial.content}"</p>
                <div>
                  <div className="font-semibold text-gray-900">{testimonial.name}</div>
                  <div className="text-sm text-gray-600">{testimonial.role}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-gray-900 to-gray-800">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold text-white mb-6">
              Ready to Transform Your Real Estate Business?
            </h2>
            <p className="text-xl text-gray-300 mb-10">
              Join thousands of professionals using ConcordBroker to stay ahead of the market
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center px-8 py-4 text-gray-900 bg-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all"
              >
                Get Started Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-flex items-center px-8 py-4 text-white border-2 border-white/30 rounded-xl font-medium hover:bg-white/10 transition-all"
              >
                Watch Demo
                <Globe className="ml-2 w-5 h-5" />
              </motion.button>
            </div>

            <div className="mt-12 flex flex-wrap justify-center gap-8 text-gray-400">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                <span>Bank-level Security</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5" />
                <span>SOC 2 Certified</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                <span>99.9% Uptime</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}