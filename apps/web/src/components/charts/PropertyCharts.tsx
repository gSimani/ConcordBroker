import React from 'react'
import { Line, Bar, Pie, Doughnut, Radar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Card } from '@/components/ui/card'
import { TrendingUp, TrendingDown, DollarSign, Home, Calendar } from 'lucide-react'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface PropertyChartsProps {
  data: any
}

export const PriceHistoryChart: React.FC<{ data: any }> = ({ data }) => {
  if (!data?.labels?.length) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Price History</h3>
        <p className="text-gray-500">No price history data available</p>
      </Card>
    )
  }

  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map((ds: any) => ({
      ...ds,
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.3,
      fill: true
    }))
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.dataset.label || ''
            const value = context.parsed.y
            return `${label}: $${value.toLocaleString()}`
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: (value: any) => `$${(value / 1000).toFixed(0)}K`
        }
      }
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Price History</h3>
        <TrendingUp className="h-5 w-5 text-green-500" />
      </div>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
    </Card>
  )
}

export const MarketComparisonChart: React.FC<{ data: any }> = ({ data }) => {
  if (!data?.labels?.length) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Market Comparison</h3>
        <p className="text-gray-500">No comparison data available</p>
      </Card>
    )
  }

  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map((ds: any, idx: number) => ({
      ...ds,
      backgroundColor: idx === 0 ?
        ['rgba(239, 68, 68, 0.8)', ...Array(data.labels.length - 1).fill('rgba(59, 130, 246, 0.6)')] :
        ['rgba(251, 191, 36, 0.8)', ...Array(data.labels.length - 1).fill('rgba(34, 197, 94, 0.6)')]
    }))
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.dataset.label || ''
            const value = context.parsed.y || context.parsed
            return `${label}: $${value.toLocaleString()}`
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: (value: any) => `$${(value / 1000).toFixed(0)}K`
        }
      }
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Market Comparison</h3>
        <Home className="h-5 w-5 text-blue-500" />
      </div>
      <div className="h-64">
        <Bar data={chartData} options={options} />
      </div>
    </Card>
  )
}

export const ROIProjectionChart: React.FC<{ data: any }> = ({ data }) => {
  if (!data?.labels?.length) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">ROI Projection</h3>
        <p className="text-gray-500">No ROI data available</p>
      </Card>
    )
  }

  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map((ds: any, idx: number) => ({
      ...ds,
      borderColor: idx === 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
      backgroundColor: idx === 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
      tension: 0.3,
      fill: true
    }))
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.dataset.label || ''
            const value = context.parsed.y
            return `${label}: ${value.toFixed(2)}%`
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: (value: any) => `${value}%`
        }
      }
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">ROI Projection (10 Years)</h3>
        <DollarSign className="h-5 w-5 text-green-500" />
      </div>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
    </Card>
  )
}

export const PortfolioDistributionChart: React.FC<{ data: any }> = ({ data }) => {
  if (!data?.county_distribution?.labels?.length && !data?.type_distribution?.labels?.length) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Portfolio Distribution</h3>
        <p className="text-gray-500">No portfolio data available</p>
      </Card>
    )
  }

  const countyChartData = data.county_distribution
  const typeChartData = data.type_distribution

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          padding: 10,
          font: {
            size: 11
          }
        }
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.label || ''
            const value = context.parsed
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
            const percentage = ((value / total) * 100).toFixed(1)
            return `${label}: ${value} (${percentage}%)`
          }
        }
      }
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {countyChartData && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">By County</h3>
          <div className="h-64">
            <Doughnut data={countyChartData} options={options} />
          </div>
        </Card>
      )}
      {typeChartData && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">By Property Type</h3>
          <div className="h-64">
            <Pie data={typeChartData} options={options} />
          </div>
        </Card>
      )}
    </div>
  )
}

export const InvestmentScoreRadar: React.FC<{ metrics: any }> = ({ metrics }) => {
  const labels = [
    'Price/Value',
    'Location',
    'Condition',
    'Cash Flow',
    'Appreciation',
    'Market Trends'
  ]

  const scores = [
    metrics.priceToAssessedRatio ? Math.min((1 / metrics.priceToAssessedRatio) * 100, 100) : 50,
    metrics.propertyAge ? Math.max(100 - metrics.propertyAge, 0) : 50,
    metrics.depreciationFactor ? metrics.depreciationFactor * 100 : 50,
    metrics.capRate ? Math.min(metrics.capRate * 1000, 100) : 50,
    metrics.priceVsComps ? Math.min((1 / metrics.priceVsComps) * 100, 100) : 50,
    metrics.pricePercentile || 50
  ]

  const data = {
    labels,
    datasets: [
      {
        label: 'Investment Score',
        data: scores,
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 2,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(59, 130, 246)'
      }
    ]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      r: {
        angleLines: {
          display: true
        },
        suggestedMin: 0,
        suggestedMax: 100,
        ticks: {
          stepSize: 20
        }
      }
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Investment Analysis</h3>
      <div className="h-64">
        <Radar data={data} options={options} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
        {labels.map((label, idx) => (
          <div key={label} className="flex justify-between">
            <span className="text-gray-600">{label}:</span>
            <span className="font-medium">{scores[idx].toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </Card>
  )
}

export const MarketTrendsChart: React.FC<{ data: any }> = ({ data }) => {
  if (!data?.monthly_averages) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Market Trends</h3>
        <p className="text-gray-500">No market trend data available</p>
      </Card>
    )
  }

  const labels = Object.keys(data.monthly_averages)
  const values = Object.values(data.monthly_averages) as number[]

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Average Sale Price',
        data: values,
        borderColor: 'rgb(147, 51, 234)',
        backgroundColor: 'rgba(147, 51, 234, 0.1)',
        tension: 0.3,
        fill: true
      }
    ]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.y
            return `Avg Price: $${value.toLocaleString()}`
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: (value: any) => `$${(value / 1000).toFixed(0)}K`
        }
      }
    }
  }

  const trendIcon = data.trend === 'increasing' ?
    <TrendingUp className="h-5 w-5 text-green-500" /> :
    <TrendingDown className="h-5 w-5 text-red-500" />

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Market Trends</h3>
        <div className="flex items-center gap-2">
          {trendIcon}
          <span className={`text-sm font-medium ${data.trend === 'increasing' ? 'text-green-500' : 'text-red-500'}`}>
            {data.total_change_percentage?.toFixed(1)}%
          </span>
        </div>
      </div>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-600">Sample Size:</span>
          <span className="ml-2 font-medium">{data.sample_size} properties</span>
        </div>
        <div>
          <span className="text-gray-600">Time Period:</span>
          <span className="ml-2 font-medium">{data.time_period_days} days</span>
        </div>
      </div>
    </Card>
  )
}

export const PropertyMetricsCards: React.FC<{ metrics: any }> = ({ metrics }) => {
  const cards = [
    {
      title: 'Price per Sq Ft',
      value: metrics.pricePerSqft ? `$${metrics.pricePerSqft.toFixed(0)}` : 'N/A',
      icon: <Home className="h-4 w-4" />,
      color: 'text-blue-600'
    },
    {
      title: 'Cap Rate',
      value: metrics.capRate ? `${(metrics.capRate * 100).toFixed(2)}%` : 'N/A',
      icon: <TrendingUp className="h-4 w-4" />,
      color: 'text-green-600'
    },
    {
      title: 'Est. Monthly Rent',
      value: metrics.estimatedMonthlyRent ? `$${metrics.estimatedMonthlyRent.toFixed(0)}` : 'N/A',
      icon: <DollarSign className="h-4 w-4" />,
      color: 'text-purple-600'
    },
    {
      title: 'Property Age',
      value: metrics.propertyAge ? `${metrics.propertyAge} years` : 'N/A',
      icon: <Calendar className="h-4 w-4" />,
      color: 'text-orange-600'
    }
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.title} className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">{card.title}</span>
            <span className={card.color}>{card.icon}</span>
          </div>
          <div className="text-xl font-bold">{card.value}</div>
        </Card>
      ))}
    </div>
  )
}

export default function PropertyCharts({ data }: PropertyChartsProps) {
  return (
    <div className="space-y-6">
      {data.metrics && <PropertyMetricsCards metrics={data.metrics} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.charts?.priceHistory && <PriceHistoryChart data={data.charts.priceHistory} />}
        {data.charts?.marketComparison && <MarketComparisonChart data={data.charts.marketComparison} />}
        {data.charts?.roiProjection && <ROIProjectionChart data={data.charts.roiProjection} />}
        {data.metrics && <InvestmentScoreRadar metrics={data.metrics} />}
      </div>

      {data.charts?.portfolioDistribution && (
        <PortfolioDistributionChart data={data.charts.portfolioDistribution} />
      )}

      {data.marketTrends && <MarketTrendsChart data={data.marketTrends} />}
    </div>
  )
}
