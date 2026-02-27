import PropTypes from 'prop-types';
import {
  AlertTriangle,
  Factory,
  Clock,
  Gauge,
  CheckCircle,
  User,
  FileText,
} from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import Button from '../common/Button';
import { formatDateTime, formatTimeAgo } from '../../utils/format';

const SEVERITY_CONFIG = {
  high: { badge: 'danger', label: 'High Severity' },
  medium: { badge: 'warning', label: 'Medium Severity' },
  low: { badge: 'info', label: 'Low Severity' },
};

function ViolationDetail({ violation, onResolve, isLoading }) {
  if (!violation) return null;

  const severity = SEVERITY_CONFIG[violation.severity] || SEVERITY_CONFIG.medium;
  const isActive = violation.status === 'active';
  const exceedancePercent = violation.threshold
    ? (((violation.measured_value - violation.threshold) / violation.threshold) * 100).toFixed(1)
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-aqi-unhealthy/10 border border-aqi-unhealthy/20 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-7 h-7 text-aqi-unhealthy" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={severity.badge} dot>
                {severity.label}
              </Badge>
              <Badge variant={isActive ? 'danger' : 'success'} dot>
                {isActive ? 'Active' : 'Resolved'}
              </Badge>
            </div>
            <h1 className="text-xl font-display font-bold text-[var(--color-text-primary)]">
              {violation.pollutant ? (
                <>
                  <span className="font-mono uppercase">{violation.pollutant}</span> Threshold Violation
                </>
              ) : (
                'Violation Report'
              )}
            </h1>
          </div>
        </div>

        {isActive && (
          <Button
            variant="primary"
            icon={CheckCircle}
            onClick={() => onResolve?.(violation.id)}
            loading={isLoading}
          >
            Resolve Violation
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Measurement Details */}
        <Card title="Measurement Details">
          <div className="space-y-4">
            {violation.measured_value != null && (
              <div>
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
                  Measured Value
                </p>
                <p className="text-2xl font-mono font-bold text-aqi-unhealthy tabular-nums">
                  {violation.measured_value}{' '}
                  <span className="text-xs text-[var(--color-text-muted)] font-sans">µg/m³</span>
                </p>
              </div>
            )}

            {violation.threshold != null && (
              <div>
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
                  Threshold Limit
                </p>
                <p className="text-2xl font-mono font-bold text-[var(--color-text-secondary)] tabular-nums">
                  {violation.threshold}{' '}
                  <span className="text-xs text-[var(--color-text-muted)] font-sans">µg/m³</span>
                </p>
              </div>
            )}

            {exceedancePercent && (
              <div className="p-3 rounded-xl bg-aqi-unhealthy/5 border border-aqi-unhealthy/20">
                <p className="text-xs text-[var(--color-text-muted)]">Exceedance</p>
                <p className="text-lg font-mono font-bold text-aqi-unhealthy">
                  +{exceedancePercent}%
                </p>
              </div>
            )}

            {/* Visual bar */}
            {violation.threshold != null && violation.measured_value != null && (
              <div>
                <div className="flex justify-between text-[10px] text-[var(--color-text-muted)] mb-1.5">
                  <span>0</span>
                  <span>Limit: {violation.threshold}</span>
                  <span>{Math.round(violation.measured_value * 1.2)}</span>
                </div>
                <div className="h-3 rounded-full bg-white/5 overflow-hidden relative">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-aqi-good via-aqi-unhealthy-sensitive to-aqi-unhealthy transition-all duration-1000"
                    style={{
                      width: `${Math.min(
                        (violation.measured_value / (violation.measured_value * 1.2)) * 100,
                        100
                      )}%`,
                    }}
                  />
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-[var(--color-text-primary)]"
                    style={{
                      left: `${(violation.threshold / (violation.measured_value * 1.2)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Violation Info */}
        <Card title="Violation Information">
          <div className="space-y-3">
            <DetailRow
              icon={Gauge}
              label="Pollutant"
              value={
                <span className="font-mono uppercase text-sm text-[var(--color-text-secondary)]">
                  {violation.pollutant || '--'}
                </span>
              }
            />
            <DetailRow
              icon={Factory}
              label="Factory"
              value={
                <span className="text-sm text-[var(--color-text-secondary)]">
                  {violation.factory_name || violation.factory_id || '--'}
                </span>
              }
            />
            <DetailRow
              icon={Clock}
              label="Detected"
              value={
                <div>
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    {formatDateTime(violation.detected_at || violation.created_at)}
                  </span>
                  <span className="block text-[10px] text-[var(--color-text-muted)]">
                    {formatTimeAgo(violation.detected_at || violation.created_at)}
                  </span>
                </div>
              }
            />
            {violation.resolved_at && (
              <DetailRow
                icon={CheckCircle}
                label="Resolved"
                value={
                  <span className="text-sm text-aqi-good">
                    {formatDateTime(violation.resolved_at)}
                  </span>
                }
              />
            )}
            {violation.resolved_by && (
              <DetailRow
                icon={User}
                label="Resolved By"
                value={
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    {violation.resolved_by}
                  </span>
                }
              />
            )}
            {violation.notes && (
              <DetailRow
                icon={FileText}
                label="Notes"
                value={
                  <p className="text-sm text-[var(--color-text-secondary)]">{violation.notes}</p>
                }
              />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function DetailRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start justify-between py-2 border-b border-[var(--color-border)] last:border-0">
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </div>
      <div className="text-right">{value}</div>
    </div>
  );
}

DetailRow.propTypes = {
  icon: PropTypes.elementType.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.node.isRequired,
};

ViolationDetail.propTypes = {
  violation: PropTypes.shape({
    id: PropTypes.string,
    severity: PropTypes.string,
    status: PropTypes.string,
    pollutant: PropTypes.string,
    measured_value: PropTypes.number,
    threshold: PropTypes.number,
    factory_id: PropTypes.string,
    factory_name: PropTypes.string,
    detected_at: PropTypes.string,
    created_at: PropTypes.string,
    resolved_at: PropTypes.string,
    resolved_by: PropTypes.string,
    notes: PropTypes.string,
  }),
  onResolve: PropTypes.func,
  isLoading: PropTypes.bool,
};

export default ViolationDetail;
