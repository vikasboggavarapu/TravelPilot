import { create } from 'zustand';

export interface Activity {
  name: string;
  category: string;
  location?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  estimated_cost: number;
  booking_required: boolean;
  booking_url?: string;
  description?: string;
  tips?: string;
  alternatives: any[];
  status: 'confirmed' | 'at_risk' | 'cancelled' | 'alternative';
  travel_to_next?: { distance_km: number; duration_minutes: number; mode: string } | null;
}

export interface ItineraryDay {
  day_id: string;
  trip_id: string;
  day_number: number;
  date: string;
  theme?: string;
  weather_summary?: string;
  weather_data?: any;
  estimated_cost: number;
  notes?: string;
  activities: Activity[];
}

export interface Trip {
  trip_id: string;
  user_id: string;
  destination: string;
  origin_city?: string;
  start_date: string;
  end_date: string;
  num_travelers: number;
  budget: number;
  currency: string;
  status: string;
  trip_preferences?: any;
}

export interface BudgetSummary {
  total_budget: number;
  currency: string;
  spent_accommodation: number;
  spent_transport: number;
  spent_food: number;
  spent_activities: number;
  total_estimated: number;
  remaining: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  agent_node?: string;
}

interface TripStore {
  // State
  currentTrip: Trip | null;
  itinerary: ItineraryDay[];
  budget: BudgetSummary | null;
  chatMessages: ChatMessage[];
  isLoading: boolean;
  isChatLoading: boolean;
  activeTab: 'dashboard' | 'itinerary' | 'backups' | 'budget' | 'weather';
  selectedDay: number | null;

  // Actions
  setCurrentTrip: (trip: Trip) => void;
  setItinerary: (days: ItineraryDay[]) => void;
  setBudget: (budget: BudgetSummary) => void;
  addChatMessage: (msg: ChatMessage) => void;
  setLoading: (v: boolean) => void;
  setChatLoading: (v: boolean) => void;
  setActiveTab: (tab: 'dashboard' | 'itinerary' | 'backups' | 'budget' | 'weather') => void;
  setSelectedDay: (day: number | null) => void;
  reset: () => void;
}

export const useTripStore = create<TripStore>((set) => ({
  currentTrip: null,
  itinerary: [],
  budget: null,
  chatMessages: [],
  isLoading: false,
  isChatLoading: false,
  activeTab: 'itinerary',
  selectedDay: null,

  setCurrentTrip: (trip) => set({ currentTrip: trip }),
  setItinerary: (days) => set({ itinerary: days }),
  setBudget: (budget) => set({ budget }),
  addChatMessage: (msg) => set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  setLoading: (v) => set({ isLoading: v }),
  setChatLoading: (v) => set({ isChatLoading: v }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSelectedDay: (day) => set({ selectedDay: day }),
  reset: () => set({
    currentTrip: null, itinerary: [], budget: null,
    chatMessages: [], isLoading: false, isChatLoading: false,
    activeTab: 'itinerary', selectedDay: null,
  }),
}));
