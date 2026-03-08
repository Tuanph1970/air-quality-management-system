import { cn } from '../../utils/cn';

/**
 * ProgressBar Component
 * Displays a progress bar with optional label
 */
export default function ProgressBar({
  progress = 0,
  className,
  showLabel = true,
  size = 'md',
}) {
  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-4',
  };

  const getColorClass = (progress) => {
    if (progress < 30) return 'bg-red-500';
    if (progress < 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className={cn('w-full bg-gray-200 rounded-full overflow-hidden', sizes[size])}>
        <div
          className={cn('h-full transition-all duration-300 ease-in-out', getColorClass(progress))}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
