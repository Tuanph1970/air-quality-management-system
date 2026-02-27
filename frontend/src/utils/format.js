import { format, formatDistanceToNow, parseISO } from 'date-fns';

export function formatDate(dateStr) {
  if (!dateStr) return '--';
  const date = typeof dateStr === 'string' ? parseISO(dateStr) : dateStr;
  return format(date, 'MMM d, yyyy');
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '--';
  const date = typeof dateStr === 'string' ? parseISO(dateStr) : dateStr;
  return format(date, 'MMM d, yyyy HH:mm');
}

export function formatTimeAgo(dateStr) {
  if (!dateStr) return '--';
  const date = typeof dateStr === 'string' ? parseISO(dateStr) : dateStr;
  return formatDistanceToNow(date, { addSuffix: true });
}

export function formatNumber(value, decimals = 1) {
  if (value == null) return '--';
  return Number(value).toFixed(decimals);
}

export function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}
