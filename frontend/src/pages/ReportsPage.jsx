import { useState } from 'react';
import {
  FileText,
  Download,
  Calendar,
  BarChart3,
  TrendingUp,
  Factory,
  AlertTriangle,
  Wind,
} from 'lucide-react';
import Header from '../components/layout/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';

const REPORT_TYPES = [
  {
    id: 'air-quality',
    title: 'Air Quality Summary',
    description: 'Daily/weekly AQI trends across all monitoring stations',
    icon: Wind,
    color: 'text-brand-400',
    bgColor: 'bg-brand-600/10 border-brand-600/20',
  },
  {
    id: 'emissions',
    title: 'Factory Emissions',
    description: 'Emission levels and compliance status for all registered factories',
    icon: Factory,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10 border-blue-500/20',
  },
  {
    id: 'violations',
    title: 'Violation Report',
    description: 'Active and resolved violations with severity breakdown',
    icon: AlertTriangle,
    color: 'text-aqi-unhealthy-sensitive',
    bgColor: 'bg-aqi-unhealthy-sensitive/10 border-aqi-unhealthy-sensitive/20',
  },
  {
    id: 'trends',
    title: 'Trend Analysis',
    description: 'Long-term pollution trends and predictive analytics',
    icon: TrendingUp,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10 border-purple-500/20',
  },
];

function ReportsPage() {
  const [selectedType, setSelectedType] = useState(null);
  const [dateRange, setDateRange] = useState({ from: '', to: '' });

  const handleGenerate = () => {
    // Report generation will be implemented when backend endpoints are ready
    // For now this is a placeholder
  };

  return (
    <>
      <Header title="Reports" subtitle="Generate and download environmental reports" />

      <main className="p-6 space-y-6">
        {/* Report Type Selection */}
        <div>
          <h3 className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
            Select Report Type
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {REPORT_TYPES.map((type) => {
              const Icon = type.icon;
              const isSelected = selectedType === type.id;

              return (
                <button
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  className={`card text-left transition-all duration-200 ${
                    isSelected
                      ? 'border-brand-500/40 bg-brand-600/5 shadow-aqi'
                      : 'hover:border-[var(--color-border-light)]'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl ${type.bgColor} border flex items-center justify-center mb-3`}>
                    <Icon className={`w-5 h-5 ${type.color}`} />
                  </div>
                  <h4 className="text-sm font-display font-semibold text-[var(--color-text-primary)] mb-1">
                    {type.title}
                  </h4>
                  <p className="text-xs text-[var(--color-text-muted)]">{type.description}</p>
                  {isSelected && (
                    <div className="w-2 h-2 rounded-full bg-brand-400 absolute top-3 right-3" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Date Range & Options */}
        <Card title="Report Configuration" subtitle="Set the date range and options for your report">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                <Calendar className="w-3 h-3 inline mr-1" />
                From Date
              </label>
              <input
                type="date"
                value={dateRange.from}
                onChange={(e) => setDateRange((prev) => ({ ...prev, from: e.target.value }))}
                className="input w-full"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                <Calendar className="w-3 h-3 inline mr-1" />
                To Date
              </label>
              <input
                type="date"
                value={dateRange.to}
                onChange={(e) => setDateRange((prev) => ({ ...prev, to: e.target.value }))}
                className="input w-full"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              icon={BarChart3}
              onClick={handleGenerate}
              disabled={!selectedType}
            >
              Generate Report
            </Button>
            <Button
              variant="secondary"
              icon={Download}
              disabled={!selectedType}
            >
              Export PDF
            </Button>
          </div>
        </Card>

        {/* Recent Reports / Empty State */}
        <Card title="Recent Reports" subtitle="Previously generated reports">
          <EmptyState
            icon={FileText}
            title="No reports generated"
            description="Select a report type and date range above to generate your first report"
          />
        </Card>
      </main>
    </>
  );
}

export default ReportsPage;
