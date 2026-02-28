import { useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts';
import { TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';

/**
 * ValidationChart - Compare sensor readings against satellite reference data
 * 
 * @param {array} data - Array of comparison data points
 * @param {string} sensorName - Name of the sensor being validated
 * @param {object} metrics - Validation metrics (correlation, bias, rmse)
 * @param {string} pollutant - Pollutant being compared
 * @param {number} tolerance - Deviation tolerance threshold (percentage)
 */
function ValidationChart({ 
  data = [], 
  sensorName = 'Sensor', 
  metrics = {}, 
  pollutant = 'PM2.5',
  tolerance = 30,
}) {
  // Process data for chart
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      deviation: point.sensor_value && point.satellite_value
        ? Math.abs(((point.sensor_value - point.satellite_value) / point.satellite_value) * 100)
        : 0,
      is_anomalous: point.sensor_value && point.satellite_value
        ? Math.abs(((point.sensor_value - point.satellite_value) / point.satellite_value) * 100) > tolerance
        : false,
    }));
  }, [data, tolerance]);

  // Calculate summary statistics
  const summary = useMemo(() => {
    if (data.length === 0) return null;

    const validPoints = data.filter(
      (p) => p.sensor_value && p.satellite_value
    );
    const anomalousPoints = validPoints.filter(
      (p) => Math.abs(((p.sensor_value - p.satellite_value) / p.satellite_value) * 100) > tolerance
    );

    return {
      total: validPoints.length,
      anomalous: anomalousPoints.length,
      anomalyRate: validPoints.length > 0 
        ? (anomalousPoints.length / validPoints.length) * 100 
        : 0,
    };
  }, [data, tolerance]);

  // Format timestamp for display
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;

    const sensorValue = payload.find((p) => p.dataKey === 'sensor_value')?.value;
    const satelliteValue = payload.find((p) => p.dataKey === 'satellite_value')?.value;
    const deviation = payload[0]?.payload?.deviation;
    const isAnomalous = payload[0]?.payload?.is_anomalous;

    return (
      <div className="card !p-3 !rounded-lg text-xs bg-slate-800 border border-slate-700">
        <p className="text-slate-400 mb-2">{label}</p>
        <div className="space-y-1">
          <div className="flex justify-between gap-4">
            <span className="text-blue-400">Sensor:</span>
            <span className="font-mono text-white">{sensorValue?.toFixed(2)} µg/m³</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-purple-400">Satellite:</span>
            <span className="font-mono text-white">{satelliteValue?.toFixed(2)} µg/m³</span>
          </div>
          <div className="flex justify-between gap-4 pt-1 border-t border-slate-700">
            <span className="text-slate-400">Deviation:</span>
            <span className={`font-mono ${deviation > tolerance ? 'text-red-400' : 'text-green-400'}`}>
              {deviation?.toFixed(1)}%
            </span>
          </div>
          {isAnomalous && (
            <div className="flex items-center gap-1 text-red-400 mt-1">
              <AlertTriangle size={12} />
              <span>Anomaly detected</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  CustomTooltip.propTypes = {
    active: PropTypes.bool,
    payload: PropTypes.array,
    label: PropTypes.string,
  };

  return (
    <Card 
      title="Sensor vs Satellite Validation" 
      icon={<TrendingUp size={20} />}
      className="h-full"
    >
      {/* Summary Stats */}
      {summary && (
        <div className="flex items-center gap-4 mb-4 pb-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <CheckCircle size={16} className="text-green-400" />
            <span className="text-sm text-slate-400">Valid:</span>
            <span className="text-lg font-bold text-white">{summary.total - summary.anomalous}</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-red-400" />
            <span className="text-sm text-slate-400">Anomalies:</span>
            <span className="text-lg font-bold text-red-400">{summary.anomalous}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">Rate:</span>
            <Badge variant={summary.anomalyRate > 20 ? 'danger' : 'success'}>
              {summary.anomalyRate.toFixed(1)}%
            </Badge>
          </div>
          <div className="ml-auto text-right">
            <div className="text-xs text-slate-400">Correlation</div>
            <div className="text-lg font-bold text-white">{metrics.correlation?.toFixed(3) || '0.000'}</div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatTime}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              label={{ value: pollutant + ' (µg/m³)', angle: -90, position: 'insideLeft', fill: '#64748b' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Tolerance threshold lines */}
            <ReferenceLine 
              y={0} 
              stroke="#64748b" 
              strokeDasharray="3 3" 
              label="Zero"
            />
            
            {/* Sensor readings */}
            <Area
              type="monotone"
              dataKey="sensor_value"
              name="Sensor"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.1}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="sensor_value"
              name="Sensor"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
            
            {/* Satellite reference */}
            <Area
              type="monotone"
              dataKey="satellite_value"
              name="Satellite"
              stroke="#a855f7"
              fill="#a855f7"
              fillOpacity={0.1}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="satellite_value"
              name="Satellite"
              stroke="#a855f7"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics Footer */}
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-700">
        <div>
          <div className="text-xs text-slate-400">Bias</div>
          <div className="text-sm font-mono text-white">{metrics.bias?.toFixed(2) || '0.00'}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">RMSE</div>
          <div className="text-sm font-mono text-white">{metrics.rmse?.toFixed(2) || '0.00'}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">MAE</div>
          <div className="text-sm font-mono text-white">{metrics.mae?.toFixed(2) || '0.00'}</div>
        </div>
      </div>
    </Card>
  );
}

ValidationChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      timestamp: PropTypes.string,
      sensor_value: PropTypes.number,
      satellite_value: PropTypes.number,
    })
  ),
  sensorName: PropTypes.string,
  metrics: PropTypes.shape({
    correlation: PropTypes.number,
    bias: PropTypes.number,
    rmse: PropTypes.number,
    mae: PropTypes.number,
  }),
  pollutant: PropTypes.string,
  tolerance: PropTypes.number,
};

export default ValidationChart;
