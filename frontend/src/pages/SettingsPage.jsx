import { useState } from 'react';
import { Bell, Shield, Palette, Globe, ChevronRight } from 'lucide-react';
import Header from '../components/layout/Header';
import LocationSettingsDialog from '../components/common/LocationSettingsDialog';
import useLocationStore from '../store/locationStore';

function SettingsPage() {
  const [locationOpen, setLocationOpen] = useState(false);
  const location = useLocationStore();

  const SETTINGS_SECTIONS = [
    {
      icon: Bell,
      label: 'Notifications',
      description: 'Configure alert thresholds and notification channels',
      onClick: null,
    },
    {
      icon: Shield,
      label: 'Security',
      description: 'Manage access control and API keys',
      onClick: null,
    },
    {
      icon: Palette,
      label: 'Display',
      description: 'Customize dashboard appearance and units',
      onClick: null,
    },
    {
      icon: Globe,
      label: 'Location &amp; Region',
      description: location.label,
      meta: `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`,
      onClick: () => setLocationOpen(true),
    },
  ];

  return (
    <div className="min-h-screen">
      <Header title="Settings" subtitle="System configuration" />

      <div className="p-6 max-w-2xl">
        <div className="space-y-3">
          {SETTINGS_SECTIONS.map((section) => {
            const Icon = section.icon;
            const clickable = !!section.onClick;
            return (
              <div
                key={section.label}
                onClick={section.onClick || undefined}
                className={`card group flex items-center gap-4 ${clickable ? 'cursor-pointer hover:border-brand-600/30 transition-colors' : ''}`}
              >
                <div className={`w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center transition-colors ${clickable ? 'group-hover:bg-brand-600/10' : ''}`}>
                  <Icon className={`w-5 h-5 transition-colors ${clickable ? 'text-[var(--color-text-muted)] group-hover:text-brand-400' : 'text-[var(--color-text-muted)]'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)]">
                    {section.label}
                  </h3>
                  <p className="text-xs text-[var(--color-text-muted)] truncate">{section.description}</p>
                </div>
                {section.meta && (
                  <span className="text-xs font-mono text-[var(--color-text-muted)] hidden sm:block">
                    {section.meta}
                  </span>
                )}
                {clickable && (
                  <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      <LocationSettingsDialog isOpen={locationOpen} onClose={() => setLocationOpen(false)} />
    </div>
  );
}

export default SettingsPage;
