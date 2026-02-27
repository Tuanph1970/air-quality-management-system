import { useEffect } from 'react';
import PropTypes from 'prop-types';

function HeatmapLayer({ map, data = [] }) {
  useEffect(() => {
    if (!map || !window.google?.maps?.visualization || data.length === 0) return;

    const heatmapData = data
      .filter((point) => point.latitude && point.longitude && point.aqi != null)
      .map((point) => ({
        location: new window.google.maps.LatLng(point.latitude, point.longitude),
        weight: point.aqi / 500,
      }));

    const heatmap = new window.google.maps.visualization.HeatmapLayer({
      data: heatmapData,
      map,
      radius: 50,
      opacity: 0.6,
      gradient: [
        'rgba(0, 228, 0, 0)',
        'rgba(0, 228, 0, 0.6)',
        'rgba(255, 255, 0, 0.7)',
        'rgba(255, 126, 0, 0.8)',
        'rgba(255, 0, 0, 0.9)',
        'rgba(143, 63, 151, 0.9)',
        'rgba(126, 0, 35, 1)',
      ],
    });

    return () => {
      heatmap.setMap(null);
    };
  }, [map, data]);

  return null;
}

HeatmapLayer.propTypes = {
  map: PropTypes.object,
  data: PropTypes.arrayOf(
    PropTypes.shape({
      latitude: PropTypes.number.isRequired,
      longitude: PropTypes.number.isRequired,
      aqi: PropTypes.number,
    })
  ),
};

export default HeatmapLayer;
