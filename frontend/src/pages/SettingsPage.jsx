import { Bell, Shield, Palette, Globe } from 'lucide-react';
import Header from '../components/layout/Header';

const SETTINGS_SECTIONS = [
  { icon: Bell, label: 'Notifications', description: 'Configure alert thresholds and notification channels' },
  { icon: Shield, label: 'Security', description: 'Manage access control and API keys' },
  { icon: Palette, label: 'Display', description: 'Customize dashboard appearance and units' },
  { icon: Globe, label: 'Regions', description: 'Manage monitored zones and geographic areas' },
];

function SettingsPage() {
  return (
    <div className="min-h-screen">
      <Header title="Settings" subtitle="System configuration" />

      <div className="p-6 max-w-2xl">
        <div className="space-y-3">
          {SETTINGS_SECTIONS.map((section) => {
            const Icon = section.icon;
            return (
              <div key={section.label} className="card group cursor-pointer flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center group-hover:bg-brand-600/10 transition-colors">
                  <Icon className="w-5 h-5 text-[var(--color-text-muted)] group-hover:text-brand-400 transition-colors" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)]">
                    {section.label}
                  </h3>
                  <p className="text-xs text-[var(--color-text-muted)]">{section.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
