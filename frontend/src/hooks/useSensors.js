import { useEffect, useCallback, useState } from 'react';
import { sensorApi } from '../services/sensorApi';

export function useSensors(autoFetch = true) {
  const [sensors, setSensors] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSensors = useCallback(async (params = {}) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await sensorApi.list(params);
      const data = response.data;
      setSensors(data.data || data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load sensors');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetchSensors();
    }
  }, [autoFetch, fetchSensors]);

  return { sensors, isLoading, error, refetch: fetchSensors };
}

export function useSensorReadings(sensorId, params = {}) {
  const [readings, setReadings] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchReadings = useCallback(async (overrideParams = {}) => {
    if (!sensorId) return;
    setIsLoading(true);
    try {
      const response = await sensorApi.getReadings(sensorId, { ...params, ...overrideParams });
      setReadings(response.data?.data || response.data || []);
    } catch (_err) {
      // Non-critical, silently handle
    } finally {
      setIsLoading(false);
    }
  }, [sensorId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchReadings();
  }, [fetchReadings]);

  return { readings, isLoading, refetch: fetchReadings };
}
