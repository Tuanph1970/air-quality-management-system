import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Satellite, RefreshCw, Clock } from 'lucide-react';
import { satelliteApi } from '../../services/satelliteApi';
import { formatDistanceToNow } from 'date-fns';
import Badge from '../common/Badge';
import Card from '../common/Card';

const SatelliteDataPanel = ({ onDataSelect }) => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchLatestData();
  }, []);

  const fetchLatestData = async () => {
    setLoading(true);
    try {
      const data = await satelliteApi.getLatestAll();
      setSources(data);
    } catch (error) {
      console.error('Failed to fetch satellite data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async (source) => {
    setRefreshing(true);
    try {
      await satelliteApi.triggerFetch({ source });
      await fetchLatestData();
    } finally {
      setRefreshing(false);
    }
  };

  const getStatusColor = (quality) => {
    switch (quality) {
      case 'good': return 'success';
      case 'medium': return 'warning';
      case 'low': return 'danger';
      default: return 'secondary';
    }
  };

  return (
    <Card title="Satellite Data Sources" icon={<Satellite size={20} />}>
      {loading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-slate-700 rounded" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {sources.map((source) => (
            <div 
              key={source.source}
              className="p-3 bg-slate-700 rounded-lg hover:bg-slate-600 cursor-pointer"
              onClick={() => onDataSelect?.(source)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium text-white">{source.source.toUpperCase()}</h4>
                  <p className="text-sm text-slate-400">{source.data_type}</p>
                </div>
                <Badge variant={getStatusColor(source.quality_flag)}>
                  {source.quality_flag}
                </Badge>
              </div>
              <div className="flex justify-between items-center mt-2 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  {formatDistanceToNow(new Date(source.observation_time), { addSuffix: true })}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRefresh(source.source);
                  }}
                  disabled={refreshing}
                  className="p-1 hover:bg-slate-500 rounded"
                >
                  <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

SatelliteDataPanel.propTypes = {
  onDataSelect: PropTypes.func
};

export default SatelliteDataPanel;
