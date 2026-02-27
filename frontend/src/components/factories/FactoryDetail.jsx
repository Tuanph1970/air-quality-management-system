import { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Factory,
  MapPin,
  Calendar,
  Activity,
  Gauge,
  Shield,
  PauseCircle,
  PlayCircle,
  AlertTriangle,
} from 'lucide-react';
import Card from '../common/Card';
import StatusBadge from '../common/StatusBadge';
import AqiBadge from '../common/AqiBadge';
import Button from '../common/Button';
import AQIGauge from '../charts/AQIGauge';
import SuspendModal from './SuspendModal';
import { formatDate, formatDateTime } from '../../utils/format';
import { getAqiLevel } from '../../utils/aqi';

function FactoryDetail({ factory, onSuspend, onResume, isLoading }) {
  const [showSuspendModal, setShowSuspendModal] = useState(false);

  if (!factory) return null;

  const level = getAqiLevel(factory.current_aqi);
  const isSuspended = factory.operational_status === 'suspended';

  const handleSuspend = async (reason) => {
    await onSuspend?.(factory.id, reason);
    setShowSuspendModal(false);
  };

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-600/10 border border-brand-600/20 flex items-center justify-center flex-shrink-0">
              <Factory className="w-7 h-7 text-brand-400" />
            </div>
            <div>
              <h1 className="text-xl font-display font-bold text-[var(--color-text-primary)]">
                {factory.name}
              </h1>
              <p className="text-sm text-[var(--color-text-muted)] font-mono">
                {factory.registration_number}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isSuspended ? (
              <Button
                variant="primary"
                icon={PlayCircle}
                onClick={() => onResume?.(factory.id)}
                loading={isLoading}
              >
                Resume Operations
              </Button>
            ) : (
              <Button
                variant="danger"
                icon={PauseCircle}
                onClick={() => setShowSuspendModal(true)}
                loading={isLoading}
              >
                Suspend
              </Button>
            )}
          </div>
        </div>

        {/* Top cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* AQI Card */}
          <Card
            variant={
              factory.current_aqi > 200 ? 'danger' :
              factory.current_aqi > 150 ? 'warning' :
              factory.current_aqi > 100 ? 'warning' :
              'good'
            }
            className="flex flex-col items-center py-8"
          >
            <AQIGauge value={factory.current_aqi} size={180} />
            <p className="text-xs text-[var(--color-text-muted)] mt-3">
              {level.description}
            </p>
          </Card>

          {/* Info Card */}
          <Card title="Factory Information">
            <div className="space-y-3">
              <InfoRow
                icon={Activity}
                label="Status"
                value={<StatusBadge status={factory.operational_status || 'offline'} />}
              />
              <InfoRow
                icon={Gauge}
                label="Current AQI"
                value={<AqiBadge value={factory.current_aqi} showLabel />}
              />
              <InfoRow
                icon={Shield}
                label="Industry"
                value={
                  <span className="text-sm text-[var(--color-text-secondary)] capitalize">
                    {factory.industry_type || '--'}
                  </span>
                }
              />
              <InfoRow
                icon={MapPin}
                label="Location"
                value={
                  <span className="text-sm text-[var(--color-text-secondary)] font-mono">
                    {factory.latitude?.toFixed(4)}, {factory.longitude?.toFixed(4)}
                  </span>
                }
              />
              <InfoRow
                icon={Calendar}
                label="Registered"
                value={
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    {formatDate(factory.created_at)}
                  </span>
                }
              />
            </div>
          </Card>

          {/* Emission Limits */}
          <Card title="Emission Limits">
            {factory.max_emissions ? (
              <div className="space-y-3">
                {Object.entries(factory.max_emissions).map(([pollutant, limit]) => (
                  <div key={pollutant} className="flex items-center justify-between">
                    <span className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider font-mono">
                      {pollutant}
                    </span>
                    <span className="text-sm text-[var(--color-text-secondary)] font-mono tabular-nums">
                      {limit} <span className="text-[10px] text-[var(--color-text-muted)]">µg/m³</span>
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--color-text-muted)]">No emission limits configured</p>
            )}
          </Card>
        </div>

        {/* Suspension History */}
        {factory.suspensions && factory.suspensions.length > 0 && (
          <Card title="Suspension History" subtitle="Past and current suspensions">
            <div className="space-y-3">
              {factory.suspensions.map((suspension, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02] border border-[var(--color-border)]"
                >
                  <AlertTriangle className="w-4 h-4 text-aqi-unhealthy-sensitive flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-[var(--color-text-secondary)]">
                      {suspension.reason}
                    </p>
                    <p className="text-[10px] text-[var(--color-text-muted)] mt-1">
                      {formatDateTime(suspension.suspended_at)}
                      {suspension.resumed_at && ` — Resumed ${formatDateTime(suspension.resumed_at)}`}
                    </p>
                  </div>
                  <StatusBadge status={suspension.resumed_at ? 'resolved' : 'suspended'} />
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      <SuspendModal
        isOpen={showSuspendModal}
        onClose={() => setShowSuspendModal(false)}
        onConfirm={handleSuspend}
        factoryName={factory.name}
        isLoading={isLoading}
      />
    </>
  );
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </div>
      <div>{value}</div>
    </div>
  );
}

InfoRow.propTypes = {
  icon: PropTypes.elementType.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.node.isRequired,
};

FactoryDetail.propTypes = {
  factory: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string.isRequired,
    registration_number: PropTypes.string,
    industry_type: PropTypes.string,
    operational_status: PropTypes.string,
    current_aqi: PropTypes.number,
    latitude: PropTypes.number,
    longitude: PropTypes.number,
    max_emissions: PropTypes.object,
    created_at: PropTypes.string,
    updated_at: PropTypes.string,
    suspensions: PropTypes.array,
  }),
  onSuspend: PropTypes.func,
  onResume: PropTypes.func,
  isLoading: PropTypes.bool,
};

export default FactoryDetail;
