import { useEffect, useCallback } from 'react';
import axios from 'axios';
import { useTripStore } from '../store/tripStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useItinerary(tripId: string) {
  const { setItinerary, setBudget, setLoading, isLoading } = useTripStore();

  const fetchItinerary = useCallback(async () => {
    if (!tripId) return;
    setLoading(true);
    try {
      const [{ data: days }, { data: dash }] = await Promise.all([
        axios.get(`${API_BASE}/itinerary/${tripId}`),
        axios.get(`${API_BASE}/dashboard/${tripId}/budget-breakdown`),
      ]);
      setItinerary(days);
      if (dash.summary) setBudget(dash.summary);
    } catch (err) {
      console.error('Failed to fetch itinerary:', err);
    } finally {
      setLoading(false);
    }
  }, [tripId, setItinerary, setBudget, setLoading]);

  useEffect(() => {
    fetchItinerary();
  }, [fetchItinerary]);

  return { refresh: fetchItinerary, isLoading };
}
