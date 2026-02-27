import { useEffect, useCallback } from 'react';
import useAlertStore from '../store/alertStore';

export function useAlerts(autoFetch = true) {
  const store = useAlertStore();

  useEffect(() => {
    if (autoFetch) {
      store.fetchViolations();
    }
  }, [autoFetch]); // eslint-disable-line react-hooks/exhaustive-deps

  const refetch = useCallback((params) => {
    store.fetchViolations(params);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    violations: store.violations,
    stats: store.stats,
    isLoading: store.isLoading,
    error: store.error,
    filters: store.filters,
    setFilters: store.setFilters,
    resolveViolation: store.resolveViolation,
    refetch,
    clearError: store.clearError,
  };
}

export function useViolation(id) {
  const store = useAlertStore();

  useEffect(() => {
    if (id) {
      store.fetchViolationById(id);
    }
    return () => store.clearSelected();
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    violation: store.selectedViolation,
    isLoading: store.isLoading,
    error: store.error,
    resolveViolation: store.resolveViolation,
  };
}
