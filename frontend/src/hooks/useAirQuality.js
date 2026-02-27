import { useEffect, useCallback, useState } from 'react';
import { airQualityApi } from '../services/airQualityApi';

export function useCurrentAqi() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetch = useCallback(async (params = {}) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await airQualityApi.getCurrentAqi(params);
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch AQI');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, isLoading, error, refetch: fetch };
}

export function useAqiForecast() {
  const [forecast, setForecast] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetch = useCallback(async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await airQualityApi.getForecast(params);
      setForecast(response.data?.data || response.data || []);
    } catch (_err) {
      // Forecast is non-critical
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { forecast, isLoading, refetch: fetch };
}

export function useAqiMapData() {
  const [mapData, setMapData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetch = useCallback(async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await airQualityApi.getMapData(params);
      setMapData(response.data?.data || response.data || []);
    } catch (_err) {
      // Map data non-critical
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { mapData, isLoading, refetch: fetch };
}

export function useAqiHistory(params = {}) {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetch = useCallback(async (overrideParams = {}) => {
    setIsLoading(true);
    try {
      const response = await airQualityApi.getHistory({ ...params, ...overrideParams });
      setHistory(response.data?.data || response.data || []);
    } catch (_err) {
      // History non-critical
    } finally {
      setIsLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { history, isLoading, refetch: fetch };
}
