import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Clock, XCircle } from 'lucide-react';
import Header from '../components/layout/Header';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { alertApi } from '../services/alertApi';
import { formatTimeAgo } from '../utils/format';

const MOCK_VIOLATIONS = [
  { id: '1', factory_name: 'Steel Plant Alpha', pollutant: 'PM2.5', measured_value: 156.2, threshold: 100.0, severity: 'high', status: 'active', created_at: new Date().toISOString() },
  { id: '2', factory_name: 'Chemical Works Beta', pollutant: 'SO2', measured_value: 0.18, threshold: 0.14, severity: 'medium', status: 'active', created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: '3', factory_name: 'Cement Factory Gamma', pollutant: 'NO2', measured_value: 0.085, threshold: 0.053, severity: 'high', status: 'active', created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: '4', factory_name: 'Power Plant Epsilon', pollutant: 'CO', measured_value: 12.8, threshold: 9.0, severity: 'low', status: 'resolved', created_at: new Date(Date.now() - 86400000).toISOString(), resolved_at: new Date(Date.now() - 43200000).toISOString() },
];

const SEVERITY_STYLES = {
  high: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400', icon: XCircle },
  medium: { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400', icon: AlertTriangle },
  low: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', text: 'text-yellow-400', icon: Clock },
};

function AlertsPage() {
  const [violations, setViolations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadViolations();
  }, []);

  async function loadViolations() {
    setIsLoading(true);
    try {
      const response = await alertApi.getViolations();
      setViolations(response.data?.data || MOCK_VIOLATIONS);
    } catch (_err) {
      setViolations(MOCK_VIOLATIONS);
    } finally {
      setIsLoading(false);
    }
  }

  const filtered = violations.filter((v) =>
    statusFilter === 'all' || v.status === statusFilter
  );

  const activeCount = violations.filter((v) => v.status === 'active').length;
  const highCount = violations.filter((v) => v.severity === 'high' && v.status === 'active').length;

  return (
    <div className="min-h-screen">
      <Header title="Alerts & Violations" subtitle={`${activeCount} active, ${highCount} high severity`} />

      <div className="p-6 space-y-5">
        {/* Summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="card border-red-500/20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <XCircle className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-display font-bold text-[var(--color-text-primary)]">{highCount}</p>
                <p className="text-xs text-[var(--color-text-muted)]">High Severity</p>
              </div>
            </div>
          </div>
          <div className="card border-orange-500/20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-display font-bold text-[var(--color-text-primary)]">{activeCount}</p>
                <p className="text-xs text-[var(--color-text-muted)]">Active Violations</p>
              </div>
            </div>
          </div>
          <div className="card border-aqi-good/20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-aqi-good/10 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-aqi-good" />
              </div>
              <div>
                <p className="text-2xl font-display font-bold text-[var(--color-text-primary)]">
                  {violations.filter((v) => v.status === 'resolved').length}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">Resolved</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filter */}
        <div className="flex gap-2">
          {['all', 'active', 'resolved'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 text-xs font-medium rounded-xl capitalize transition-all ${
                statusFilter === status
                  ? 'bg-brand-600/10 text-brand-400 border border-brand-600/20'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] border border-transparent hover:bg-white/[0.03]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Violations list */}
        {isLoading ? (
          <LoadingSpinner className="py-20" size="lg" />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={AlertTriangle}
            title="No violations"
            description="All facilities operating within limits"
          />
        ) : (
          <div className="space-y-3">
            {filtered.map((violation, index) => {
              const style = SEVERITY_STYLES[violation.severity] || SEVERITY_STYLES.low;
              const Icon = style.icon;
              const isResolved = violation.status === 'resolved';

              return (
                <div
                  key={violation.id}
                  className={`card flex items-center gap-4 ${style.border} ${isResolved ? 'opacity-60' : ''} animate-slide-up stagger-${Math.min(index + 1, 6)}`}
                >
                  <div className={`w-10 h-10 rounded-xl ${style.bg} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-5 h-5 ${style.text}`} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <h4 className="text-sm font-display font-semibold text-[var(--color-text-primary)] truncate">
                        {violation.factory_name}
                      </h4>
                      <span className={`text-[10px] font-mono uppercase font-bold px-1.5 py-0.5 rounded ${style.bg} ${style.text}`}>
                        {violation.severity}
                      </span>
                      {isResolved && (
                        <span className="text-[10px] font-mono uppercase font-bold px-1.5 py-0.5 rounded bg-aqi-good/10 text-aqi-good">
                          resolved
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      <span className="font-mono">{violation.pollutant}</span>
                      {' '} - Measured: <span className="font-mono text-[var(--color-text-secondary)]">{violation.measured_value}</span>
                      {' '} / Threshold: <span className="font-mono">{violation.threshold}</span>
                    </p>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-[var(--color-text-muted)]">{formatTimeAgo(violation.created_at)}</p>
                    {!isResolved && (
                      <button className="btn-ghost text-xs px-2 py-1 mt-1 text-brand-400">
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default AlertsPage;
