import { useState, useEffect, useCallback } from 'react';
import { fetchForecast, fetchVerificationReport } from '../services/api';

export function useForecast(date, leadTime) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchForecast(date, leadTime);
      setData(result);
    } catch (err) {
      console.error('Forecast fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [date, leadTime]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, refetch: load };
}

export function useVerification(date, leadTime) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchVerificationReport(date, leadTime);
      setData(result);
    } catch (err) {
      console.error('Verification fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [date, leadTime]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, refetch: load };
}
