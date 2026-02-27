/**
 * AQI utility functions for color coding and categorization.
 * Based on EPA AQI breakpoints.
 */

export const AQI_LEVELS = [
  { min: 0, max: 50, label: 'Good', color: '#00e400', bgClass: 'aqi-badge-good', description: 'Air quality is satisfactory.' },
  { min: 51, max: 100, label: 'Moderate', color: '#ffff00', bgClass: 'aqi-badge-moderate', description: 'Acceptable for most.' },
  { min: 101, max: 150, label: 'Unhealthy for Sensitive Groups', color: '#ff7e00', bgClass: 'aqi-badge-unhealthy-sensitive', description: 'Sensitive groups may be affected.' },
  { min: 151, max: 200, label: 'Unhealthy', color: '#ff0000', bgClass: 'aqi-badge-unhealthy', description: 'Everyone may be affected.' },
  { min: 201, max: 300, label: 'Very Unhealthy', color: '#8f3f97', bgClass: 'aqi-badge-very-unhealthy', description: 'Health alert for everyone.' },
  { min: 301, max: 500, label: 'Hazardous', color: '#7e0023', bgClass: 'aqi-badge-hazardous', description: 'Emergency conditions.' },
];

export function getAqiLevel(value) {
  if (value == null || value < 0) return AQI_LEVELS[0];
  return AQI_LEVELS.find((level) => value >= level.min && value <= level.max) || AQI_LEVELS[5];
}

export function getAqiColor(value) {
  return getAqiLevel(value).color;
}

export function getAqiBadgeClass(value) {
  return getAqiLevel(value).bgClass;
}

export function getAqiLabel(value) {
  return getAqiLevel(value).label;
}

export function formatAqi(value) {
  if (value == null) return '--';
  return Math.round(value).toString();
}
