import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Satellite, Wifi, WifiOff, Clock, RefreshCw, AlertTriangle } from 'lucide-react';
import { satelliteApi } from '../../services/satelliteApi';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { formatDistanceToNow } from 'date-fns';

/**
 * DataSourceStatus - Display status of each satellite data source
 * 
 * @param {boolean} compact - Show compact version
 * @param {function} onRefresh - Callback when refresh is triggered
 */
function DataSourceStatus({ compact = false, onRefresh }) {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const sourceList = [
        { id: 'cams_pm25', name: 'CAMS PM2.5', type: 'satellite' },
        { id: 'cams_pm10', name: 'CAMS PM10', type: 'satellite' },
        { id: 'modis_terra', name: 'MODIS Terra', type: 'satellite' },
        { id: 'modis_aqua', name: 'MODIS Aqua', type: 'satellite' },
        { id: 'tropomi_no2', name: 'TROPOMI NO₂', type: 'satellite' },
        { id: 'tropomi_so2', name: 'TROPOMI SO₂', type: 'satellite' },
      ];

      const results = await Promise.all(
        sourceList.map(async (source) => {
          try {
            const data = await satelliteApi.getLatest(source.id);
            return {
              ...source,
              status: 'online',
              lastUpdate: data?.observation_time || null,
              quality: data?.quality_flag || 'unknown',
              data: data,
            };
          } catch {
            return {
              ...source,
              status: 'offline',
              lastUpdate: null,
              quality: 'unknown',
              data: null,
            };
          }
        })
      );

      setSources(results);
    } catch (error) {
      console.error('Failed to fetch data source status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async (sourceId) => {
    setRefreshing(true);
    try {
      await satelliteApi.triggerFetch({ source: sourceId });
      await fetchStatus();
      onRefresh?.(sourceId);
    } catch (error) {
      console.error('Failed to refresh:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getStatusColor = (status, quality) => {
    if (status === 'offline') return 'danger';
    switch (quality) {
      case 'good':
        return 'success';
      case 'medium':
        return 'warning';
      case 'low':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  const getStatusLabel = (status, lastUpdate) => {
    if (status === 'offline') return 'Offline';
    if (!lastUpdate) return 'No Data';
    
    const hoursSince = Math.floor((Date.now() - new Date(lastUpdate).getTime()) / 3600000);
    if (hoursSince < 1) return 'Live';
    if (hoursSince < 6) return 'Recent';
    if (hoursSince < 24) return 'Stale';
    return 'Old';
  };

  if (loading) {
    return (
      <Card title="Data Source Status" icon={<Satellite size={20} />}>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-slate-700 rounded" />
          ))}
        </div>
      </Card>
    );
  }

  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        {sources.map((source) => (
          <div
            key={source.id}
            className={`
              flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs
              ${source.status === 'online' 
                ? 'bg-green-600/20 text-green-400 border border-green-600/30' 
                : 'bg-red-600/20 text-red-400 border border-red-600/30'
              }
            `}
            title={source.lastUpdate ? `Last update: ${formatDistanceToNow(new Date(source.lastUpdate), { addSuffix: true })}` : 'No data'}
          >
            {source.status === 'online' ? <Wifi size={12} /> : <WifiOff size={12} />}
            <span className="font-medium">{source.name.split(' ')[0]}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <Card title="Data Source Status" icon={<Satellite size={20} />}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-slate-400">Satellite data feed status</p>
        <button
          onClick={fetchStatus}
          disabled={refreshing}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="space-y-2">
        {sources.map((source) => {
          const isOnline = source.status === 'online';
          const label = getStatusLabel(source.status, source.lastUpdate);
          
          return (
            <div
              key={source.id}
              className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-slate-700/50 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isOnline ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
                  {isOnline ? <Wifi size={16} /> : <WifiOff size={16} />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">{source.name}</span>
                    <Badge variant={getStatusColor(source.status, source.quality)}>
                      {label}
                    </Badge>
                  </div>
                  {source.lastUpdate && (
                    <div className="flex items-center gap-1 text-xs text-slate-500 mt-1">
                      <Clock size={10} />
                      {formatDistanceToNow(new Date(source.lastUpdate), { addSuffix: true })}
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={() => handleRefresh(source.id)}
                disabled={refreshing || !isOnline}
                className={`
                  p-2 rounded-lg transition-colors
                  ${refreshing || !isOnline
                    ? 'text-slate-600 cursor-not-allowed'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700'
                  }
                `}
              >
                <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">
            {sources.filter((s) => s.status === 'online').length} of {sources.length} sources online
          </span>
          {sources.some((s) => s.status === 'offline') && (
            <div className="flex items-center gap-1 text-amber-400">
              <AlertTriangle size={12} />
              <span>Some sources unavailable</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

DataSourceStatus.propTypes = {
  compact: PropTypes.bool,
  onRefresh: PropTypes.func,
};

export default DataSourceStatus;
