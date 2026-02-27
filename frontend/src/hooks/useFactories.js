import { useEffect, useCallback } from 'react';
import useFactoryStore from '../store/factoryStore';

export function useFactories(autoFetch = true) {
  const store = useFactoryStore();

  useEffect(() => {
    if (autoFetch && store.factories.length === 0) {
      store.fetchFactories();
    }
  }, [autoFetch]); // eslint-disable-line react-hooks/exhaustive-deps

  const refetch = useCallback((params) => {
    store.fetchFactories(params);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    factories: store.factories,
    isLoading: store.isLoading,
    error: store.error,
    pagination: store.pagination,
    filters: store.filters,
    setFilters: store.setFilters,
    setPage: store.setPage,
    refetch,
    clearError: store.clearError,
  };
}

export function useFactory(id) {
  const store = useFactoryStore();

  useEffect(() => {
    if (id) {
      store.fetchFactoryById(id);
    }
    return () => store.clearSelected();
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    factory: store.selectedFactory,
    isLoading: store.isLoading,
    error: store.error,
    suspendFactory: store.suspendFactory,
    resumeFactory: store.resumeFactory,
  };
}
