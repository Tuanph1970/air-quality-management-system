import PropTypes from 'prop-types';
import { Activity } from 'lucide-react';

function Loading({ fullScreen = false, message = 'Loading...' }) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-500/20 to-emerald-400/20 flex items-center justify-center">
          <Activity className="w-6 h-6 text-brand-400 animate-pulse" />
        </div>
        <div className="absolute inset-0 rounded-2xl border-2 border-brand-500/20 animate-ping" />
      </div>
      <p className="text-sm text-[var(--color-text-muted)] font-medium">{message}</p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--color-bg-primary)]">
        {content}
      </div>
    );
  }

  return <div className="flex items-center justify-center py-20">{content}</div>;
}

Loading.propTypes = {
  fullScreen: PropTypes.bool,
  message: PropTypes.string,
};

export default Loading;
