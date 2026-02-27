import { useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Wind,
  Factory,
  Radio,
  AlertTriangle,
  Eye,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Header from '../components/layout/Header';
import StatCard from '../components/common/StatCard';
import AqiBadge from '../components/common/AqiBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import EmptyState from '../components/common/EmptyState';
import useDashboardStore from '../store/dashboardStore';
import { formatTimeAgo } from '../utils/format';
import { getAqiLevel } from '../utils/aqi';

// Mock data for initial display before API is connected
const MOCK_CHART_DATA = [
  { time: '00:00', aqi: 42, pm25: 12.1 },
  { time: '04:00', aqi: 38, pm25: 10.5 },
  { time: '08:00', aqi: 65, pm25: 18.3 },
  { time: '12:00', aqi: 78, pm25: 24.1 },
  { time: '16:00', aqi: 55, pm25: 16.8 },
  { time: '20:00', aqi: 48, pm25: 13.2 },
  { time: 'Now', aqi: 45, pm25: 12.8 },
];

const MOCK_VIOLATIONS = [
  { id: 1, factory_name: 'Steel Plant Alpha', pollutant: 'PM2.5', severity: 'high', created_at: new Date().toISOString() },
  { id: 2, factory_name: 'Chemical Works Beta', pollutant: 'SO2', severity: 'medium', created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 3, factory_name: 'Cement Factory Gamma', pollutant: 'NO2', severity: 'low', created_at: new Date(Date.now() - 7200000).toISOString() },
];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card !p-3 !rounded-lg text-xs">
      <p className="text-[var(--color-text-muted)] mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="font-mono" style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
}

CustomTooltip.propTypes = {
  active: PropTypes.bool,
  payload: PropTypes.array,
  label: PropTypes.string,
};

function DashboardPage() {
  const { currentAqi, activeViolations, factories, isLoading, fetchDashboardData } = useDashboardStore();

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const aqiValue = currentAqi?.aqi ?? 45;
  const aqiLevel = getAqiLevel(aqiValue);
  const violations = activeViolations.length > 0 ? activeViolations : MOCK_VIOLATIONS;

  return (
    <div className="min-h-screen">
      <Header title="Dashboard" subtitle="Real-time air quality monitoring" />

      <div className="p-6 space-y-6">
        {/* Hero AQI Display */}
        <div
          className="card relative overflow-hidden"
          style={{ borderColor: `${aqiLevel.color}20` }}
        >
          {/* Ambient glow */}
          <div
            className="absolute top-0 right-0 w-64 h-64 rounded-full blur-[100px] opacity-10"
            style={{ backgroundColor: aqiLevel.color }}
          />

          <div className="relative flex items-center justify-between">
            <div>
              <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-widest mb-2">
                Current Air Quality Index
              </p>
              <div className="flex items-end gap-4">
                <span
                  className="text-display-xl font-display font-bold font-mono tabular-nums"
                  style={{ color: aqiLevel.color }}
                >
                  {aqiValue}
                </span>
                <div className="mb-2">
                  <AqiBadge value={aqiValue} showLabel size="md" />
                  <p className="text-xs text-[var(--color-text-muted)] mt-1.5">
                    {aqiLevel.description}
                  </p>
                </div>
              </div>
            </div>

            <div className="hidden md:flex items-center gap-8 text-center">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">PM2.5</p>
                <p className="text-lg font-display font-bold font-mono text-[var(--color-text-primary)]">
                  12.8
                </p>
                <p className="text-[10px] text-[var(--color-text-muted)]">ug/m3</p>
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">PM10</p>
                <p className="text-lg font-display font-bold font-mono text-[var(--color-text-primary)]">
                  24.5
                </p>
                <p className="text-[10px] text-[var(--color-text-muted)]">ug/m3</p>
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">O3</p>
                <p className="text-lg font-display font-bold font-mono text-[var(--color-text-primary)]">
                  0.035
                </p>
                <p className="text-[10px] text-[var(--color-text-muted)]">ppm</p>
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">SO2</p>
                <p className="text-lg font-display font-bold font-mono text-[var(--color-text-primary)]">
                  0.008
                </p>
                <p className="text-[10px] text-[var(--color-text-muted)]">ppm</p>
              </div>
            </div>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Active Sensors"
            value="24"
            icon={Radio}
            trend={-2}
            trendLabel="vs last week"
            variant="good"
            className="animate-slide-up stagger-1"
          />
          <StatCard
            label="Monitored Factories"
            value={factories.length || '18'}
            icon={Factory}
            trendLabel="in system"
            className="animate-slide-up stagger-2"
          />
          <StatCard
            label="Active Violations"
            value={violations.length}
            icon={AlertTriangle}
            trend={12}
            trendLabel="vs last week"
            variant={violations.length > 5 ? 'danger' : 'warning'}
            className="animate-slide-up stagger-3"
          />
          <StatCard
            label="Avg. AQI Today"
            value="52"
            icon={Wind}
            trend={-8}
            trendLabel="improving"
            variant="good"
            className="animate-slide-up stagger-4"
          />
        </div>

        {/* Charts and violations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* AQI Trend Chart */}
          <div className="lg:col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)]">
                  AQI Trend
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">Last 24 hours</p>
              </div>
              <div className="flex gap-1">
                {['24h', '7d', '30d'].map((period) => (
                  <button
                    key={period}
                    className={`px-3 py-1 text-xs rounded-lg font-mono transition-colors ${
                      period === '24h'
                        ? 'bg-brand-600/10 text-brand-400 border border-brand-600/20'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] hover:bg-white/[0.03]'
                    }`}
                  >
                    {period}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={MOCK_CHART_DATA}>
                  <defs>
                    <linearGradient id="aqiGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="pm25Gradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis
                    dataKey="time"
                    stroke="var(--color-text-muted)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="var(--color-text-muted)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="aqi"
                    name="AQI"
                    stroke="#22c55e"
                    strokeWidth={2}
                    fill="url(#aqiGradient)"
                  />
                  <Area
                    type="monotone"
                    dataKey="pm25"
                    name="PM2.5"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fill="url(#pm25Gradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Violations */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)]">
                  Recent Violations
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">Active alerts</p>
              </div>
              <button className="btn-ghost text-xs px-2 py-1 rounded-lg">
                <Eye className="w-3.5 h-3.5 mr-1" />
                View all
              </button>
            </div>

            {isLoading ? (
              <LoadingSpinner className="py-10" />
            ) : violations.length === 0 ? (
              <EmptyState
                icon={AlertTriangle}
                title="No active violations"
                description="All factories are within emission limits"
              />
            ) : (
              <div className="space-y-3">
                {violations.map((violation) => (
                  <div
                    key={violation.id}
                    className="p-3 rounded-xl bg-white/[0.02] border border-[var(--color-border)]/50 hover:border-[var(--color-border)] transition-colors"
                  >
                    <div className="flex items-start justify-between mb-1.5">
                      <p className="text-sm font-medium text-[var(--color-text-primary)] truncate pr-2">
                        {violation.factory_name}
                      </p>
                      <span
                        className={`text-[10px] font-mono uppercase font-bold px-1.5 py-0.5 rounded ${
                          violation.severity === 'high'
                            ? 'bg-red-500/15 text-red-400'
                            : violation.severity === 'medium'
                            ? 'bg-orange-500/15 text-orange-400'
                            : 'bg-yellow-500/15 text-yellow-400'
                        }`}
                      >
                        {violation.severity}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
                      <span className="font-mono">{violation.pollutant}</span>
                      <span>{formatTimeAgo(violation.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
