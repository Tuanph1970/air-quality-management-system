import { useState } from 'react';
import PropTypes from 'prop-types';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import Header from '../components/layout/Header';
import AqiBadge from '../components/common/AqiBadge';
import { AQI_LEVELS } from '../utils/aqi';

const HOURLY_DATA = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, '0')}:00`,
  aqi: Math.round(35 + Math.sin(i / 4) * 25 + Math.random() * 15),
  pm25: +(8 + Math.sin(i / 4) * 8 + Math.random() * 5).toFixed(1),
  pm10: +(15 + Math.sin(i / 4) * 12 + Math.random() * 8).toFixed(1),
}));

const FORECAST_DATA = [
  { day: 'Mon', aqi: 48, condition: 'Good' },
  { day: 'Tue', aqi: 55, condition: 'Moderate' },
  { day: 'Wed', aqi: 72, condition: 'Moderate' },
  { day: 'Thu', aqi: 61, condition: 'Moderate' },
  { day: 'Fri', aqi: 45, condition: 'Good' },
  { day: 'Sat', aqi: 38, condition: 'Good' },
  { day: 'Sun', aqi: 42, condition: 'Good' },
];

const POLLUTANT_DATA = [
  { name: 'PM2.5', value: 12.8, unit: 'ug/m3', limit: 35, percentage: 37 },
  { name: 'PM10', value: 24.5, unit: 'ug/m3', limit: 150, percentage: 16 },
  { name: 'O3', value: 0.035, unit: 'ppm', limit: 0.07, percentage: 50 },
  { name: 'SO2', value: 0.008, unit: 'ppm', limit: 0.075, percentage: 11 },
  { name: 'NO2', value: 0.025, unit: 'ppm', limit: 0.053, percentage: 47 },
  { name: 'CO', value: 1.2, unit: 'ppm', limit: 9.0, percentage: 13 },
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

function AirQualityPage() {
  const [timeRange, setTimeRange] = useState('24h');

  return (
    <div className="min-h-screen">
      <Header title="Air Quality" subtitle="Comprehensive air quality monitoring and analysis" />

      <div className="p-6 space-y-6">
        {/* AQI Scale Reference */}
        <div className="card">
          <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)] mb-4">
            AQI Scale Reference
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {AQI_LEVELS.map((level) => (
              <div
                key={level.label}
                className="p-3 rounded-xl border transition-colors"
                style={{
                  borderColor: `${level.color}25`,
                  backgroundColor: `${level.color}08`,
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: level.color, boxShadow: `0 0 8px ${level.color}40` }}
                  />
                  <span className="text-xs font-mono font-bold" style={{ color: level.color }}>
                    {level.min}-{level.max}
                  </span>
                </div>
                <p className="text-[11px] text-[var(--color-text-secondary)] font-medium leading-tight">
                  {level.label}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Pollutant Breakdown */}
        <div className="card">
          <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)] mb-4">
            Pollutant Levels
          </h3>
          <div className="space-y-4">
            {POLLUTANT_DATA.map((pollutant) => {
              const barColor = pollutant.percentage > 75 ? '#ff0000' :
                pollutant.percentage > 50 ? '#ff7e00' : '#22c55e';

              return (
                <div key={pollutant.name}>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-mono font-bold text-[var(--color-text-primary)] w-12">
                        {pollutant.name}
                      </span>
                      <span className="text-xs text-[var(--color-text-muted)]">
                        {pollutant.value} {pollutant.unit}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-[var(--color-text-muted)]">
                      {pollutant.percentage}% of limit
                    </span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-out"
                      style={{
                        width: `${pollutant.percentage}%`,
                        backgroundColor: barColor,
                        boxShadow: `0 0 8px ${barColor}40`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Hourly trend */}
          <div className="lg:col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)]">
                  Hourly Readings
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">AQI, PM2.5, PM10</p>
              </div>
              <div className="flex gap-1">
                {['24h', '7d', '30d'].map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={`px-3 py-1 text-xs rounded-lg font-mono transition-colors ${
                      timeRange === range
                        ? 'bg-brand-600/10 text-brand-400 border border-brand-600/20'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] hover:bg-white/[0.03]'
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={HOURLY_DATA}>
                  <defs>
                    <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="pm25Grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="pm10Grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a855f7" stopOpacity={0.1} />
                      <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="hour" stroke="var(--color-text-muted)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="var(--color-text-muted)" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
                  <Area type="monotone" dataKey="aqi" name="AQI" stroke="#22c55e" strokeWidth={2} fill="url(#aqiGrad)" />
                  <Area type="monotone" dataKey="pm25" name="PM2.5" stroke="#3b82f6" strokeWidth={1.5} fill="url(#pm25Grad)" />
                  <Area type="monotone" dataKey="pm10" name="PM10" stroke="#a855f7" strokeWidth={1.5} fill="url(#pm10Grad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 7-Day Forecast */}
          <div className="card">
            <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)] mb-4">
              7-Day Forecast
            </h3>
            <div className="space-y-3">
              {FORECAST_DATA.map((day, i) => (
                <div
                  key={day.day}
                  className="flex items-center justify-between p-2.5 rounded-lg hover:bg-white/[0.02] transition-colors"
                >
                  <span className="text-sm font-medium text-[var(--color-text-secondary)] w-10">
                    {day.day}
                  </span>
                  <div className="flex-1 mx-4">
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${(day.aqi / 150) * 100}%`,
                          backgroundColor: day.aqi <= 50 ? '#22c55e' : day.aqi <= 100 ? '#ffff00' : '#ff7e00',
                          animationDelay: `${i * 100}ms`,
                        }}
                      />
                    </div>
                  </div>
                  <AqiBadge value={day.aqi} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AirQualityPage;
