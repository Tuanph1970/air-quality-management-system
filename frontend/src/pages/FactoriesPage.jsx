import { useEffect, useState } from 'react';
import { Factory, Plus, Search, MapPin, ArrowUpRight } from 'lucide-react';
import Header from '../components/layout/Header';
import StatusBadge from '../components/common/StatusBadge';
import AqiBadge from '../components/common/AqiBadge';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { factoryApi } from '../services/factoryApi';
import { formatDate } from '../utils/format';

const MOCK_FACTORIES = [
  { id: '1', name: 'Steel Plant Alpha', registration_number: 'REG-001', industry_type: 'Steel Manufacturing', operational_status: 'active', latitude: 21.028, longitude: 105.854, current_aqi: 42, created_at: '2024-01-15T00:00:00Z' },
  { id: '2', name: 'Chemical Works Beta', registration_number: 'REG-002', industry_type: 'Chemical Processing', operational_status: 'warning', latitude: 21.032, longitude: 105.849, current_aqi: 128, created_at: '2024-02-20T00:00:00Z' },
  { id: '3', name: 'Cement Factory Gamma', registration_number: 'REG-003', industry_type: 'Cement Production', operational_status: 'critical', latitude: 21.025, longitude: 105.860, current_aqi: 185, created_at: '2024-03-10T00:00:00Z' },
  { id: '4', name: 'Textile Mill Delta', registration_number: 'REG-004', industry_type: 'Textile Manufacturing', operational_status: 'suspended', latitude: 21.035, longitude: 105.842, current_aqi: 0, created_at: '2024-04-05T00:00:00Z' },
  { id: '5', name: 'Power Plant Epsilon', registration_number: 'REG-005', industry_type: 'Power Generation', operational_status: 'active', latitude: 21.020, longitude: 105.870, current_aqi: 65, created_at: '2024-05-18T00:00:00Z' },
];

function FactoriesPage() {
  const [factories, setFactories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadFactories();
  }, []);

  async function loadFactories() {
    setIsLoading(true);
    try {
      const response = await factoryApi.list();
      setFactories(response.data?.data || MOCK_FACTORIES);
    } catch (_err) {
      setFactories(MOCK_FACTORIES);
    } finally {
      setIsLoading(false);
    }
  }

  const filtered = factories.filter((f) => {
    const matchesSearch = f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.registration_number.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || f.operational_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen">
      <Header title="Factories" subtitle={`${factories.length} registered facilities`} />

      <div className="p-6 space-y-5">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search factories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-9"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-auto"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
              <option value="suspended">Suspended</option>
            </select>

            <button className="btn-primary">
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">Add Factory</span>
            </button>
          </div>
        </div>

        {/* Factory List */}
        {isLoading ? (
          <LoadingSpinner className="py-20" size="lg" />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Factory}
            title="No factories found"
            description="Try adjusting your search or filter criteria"
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map((factory, index) => (
              <div
                key={factory.id}
                className={`card group cursor-pointer animate-slide-up stagger-${Math.min(index + 1, 6)}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center group-hover:bg-white/[0.08] transition-colors">
                      <Factory className="w-5 h-5 text-[var(--color-text-muted)]" />
                    </div>
                    <div>
                      <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)] group-hover:text-brand-400 transition-colors">
                        {factory.name}
                      </h3>
                      <p className="text-[11px] font-mono text-[var(--color-text-muted)]">
                        {factory.registration_number}
                      </p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--color-text-muted)]">Industry</span>
                    <span className="text-[var(--color-text-secondary)]">{factory.industry_type}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--color-text-muted)]">Status</span>
                    <StatusBadge status={factory.operational_status} />
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--color-text-muted)]">Current AQI</span>
                    {factory.current_aqi > 0 ? (
                      <AqiBadge value={factory.current_aqi} />
                    ) : (
                      <span className="text-[var(--color-text-muted)] font-mono">--</span>
                    )}
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--color-text-muted)]">Location</span>
                    <span className="text-[var(--color-text-secondary)] flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {factory.latitude?.toFixed(3)}, {factory.longitude?.toFixed(3)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--color-text-muted)]">Registered</span>
                    <span className="text-[var(--color-text-secondary)]">{formatDate(factory.created_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default FactoriesPage;
