import PropTypes from 'prop-types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

/**
 * TimeSeriesChart - Displays air quality readings over time
 * Used for station detail view showing AQI, PM2.5, PM10 trends
 */
function TimeSeriesChart({ data = [], height = 200, showLegend = true }) {
  // Transform data for chart
  const chartData = data.map((reading) => ({
    time: new Date(reading.reading_time).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    }),
    aqi: reading.aqi ? Math.round(reading.aqi) : null,
    pm25: reading.pm25 ? reading.pm25.toFixed(1) : null,
    pm10: reading.pm10 ? reading.pm10.toFixed(1) : null,
  }));

  // Custom tooltip
  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;

    return (
      <div className="bg-[var(--color-bg-card)] border border-white/20 rounded-lg p-3 text-xs shadow-xl">
        <p className="text-gray-400 mb-2 font-medium">{label}</p>
        {payload.map((entry) => (
          <div key={entry.name} className="flex items-center gap-2 py-0.5">
            <span 
              className="w-2 h-2 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-300">{entry.name}:</span>
            <span className="font-mono font-medium" style={{ color: entry.color }}>
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  }

  CustomTooltip.propTypes = {
    active: PropTypes.bool,
    payload: PropTypes.array,
    label: PropTypes.string,
  };

  const series = [
    { key: 'aqi', name: 'AQI', color: '#22c55e' },
    { key: 'pm25', name: 'PM2.5', color: '#3b82f6' },
    { key: 'pm10', name: 'PM10', color: '#f59e0b' },
  ];

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis
            dataKey="time"
            stroke="var(--color-text-muted)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--color-text-muted)' }}
          />
          <YAxis
            stroke="var(--color-text-muted)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--color-text-muted)' }}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ 
                fontSize: '11px', 
                color: 'var(--color-text-muted)',
                paddingTop: '10px',
              }}
            />
          )}
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

TimeSeriesChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      reading_time: PropTypes.string.isRequired,
      aqi: PropTypes.number,
      pm25: PropTypes.number,
      pm10: PropTypes.number,
    })
  ),
  height: PropTypes.number,
  showLegend: PropTypes.bool,
};

export default TimeSeriesChart;
