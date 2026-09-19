import { useCallback, useRef } from 'react';
import axios from 'axios';
import { useTripStore, ChatMessage } from '../store/tripStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useChat(tripId: string) {
  const { addChatMessage, setItinerary, setBudget, setChatLoading, isChatLoading } = useTripStore();
  const wsRef = useRef<WebSocket | null>(null);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isChatLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    addChatMessage(userMsg);
    setChatLoading(true);

    try {
      const { data } = await axios.post(`${API_BASE}/chat/${tripId}`, {
        trip_id: tripId,
        message: text,
      });

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        agent_node: data.agent_node,
      };
      addChatMessage(assistantMsg);

      // If itinerary was updated, re-fetch
      if (data.itinerary_updated) {
        const { data: itinerary } = await axios.get(`${API_BASE}/itinerary/${tripId}`);
        setItinerary(itinerary);
      }

      // If budget was updated, re-fetch dashboard
      if (data.budget_updated) {
        const { data: dash } = await axios.get(`${API_BASE}/dashboard/${tripId}/budget-breakdown`);
        if (dash.summary) setBudget(dash.summary);
      }

    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err?.response?.data?.detail || err.message}. Please try again.`,
        timestamp: new Date().toISOString(),
      };
      addChatMessage(errMsg);
    } finally {
      setChatLoading(false);
    }
  }, [tripId, isChatLoading, addChatMessage, setChatLoading, setItinerary, setBudget]);

  const loadHistory = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/chat/${tripId}/history`);
      const msgs: ChatMessage[] = data.map((m: any) => ({
        id: m.message_id,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
        agent_node: m.agent_node,
      }));
      msgs.forEach(addChatMessage);
    } catch { /* ignore */ }
  }, [tripId, addChatMessage]);

  return { sendMessage, loadHistory, isLoading: isChatLoading };
}
