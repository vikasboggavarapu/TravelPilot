import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Plane, ArrowLeft, Download, RefreshCw } from 'lucide-react';
import { useTripStore } from '../store/tripStore';
import { useChat } from '../hooks/useChat';
import { useItinerary } from '../hooks/useItinerary';
import ChatPanel from '../components/ChatPanel';
import ItineraryView from '../components/ItineraryView';
import BackupOptionsView from '../components/BackupOptionsView';
import BudgetTracker from '../components/BudgetTracker';
import WeatherWidget from '../components/WeatherWidget';
import Dashboard from '../components/Dashboard';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const TABS = [
  { id: 'dashboard', label: '📊 Overview' },
  { id: 'itinerary', label: '📅 Itinerary' },
  { id: 'backups', label: '🛡️ Backup Options' },
  { id: 'budget', label: '💰 Budget' },
  { id: 'weather', label: '🌤️ Weather' },
] as const;

export default function TripView() {
  const { tripId } = useParams<{ tripId: string }>();
  const navigate = useNavigate();
  const { currentTrip, setCurrentTrip, activeTab, setActiveTab, isLoading } = useTripStore();
  const { sendMessage, loadHistory } = useChat(tripId!);
  const { refresh } = useItinerary(tripId!);

  // Load trip info if not in store
  useEffect(() => {
    if (!currentTrip && tripId) {
      axios.get(`${API_BASE}/trips/${tripId}`)
        .then(({ data }) => setCurrentTrip(data))
        .catch(() => navigate('/'));
    }
  }, [tripId, currentTrip, setCurrentTrip, navigate]);

  // Load chat history on mount
  useEffect(() => {
    if (tripId) loadHistory();
  }, [tripId]);

  // Auto-trigger initial planning if itinerary is empty
  useEffect(() => {
    if (currentTrip && tripId) {
      const firstMsg = `Plan my complete trip to ${currentTrip.destination} from ${currentTrip.start_date} to ${currentTrip.end_date}. Budget is ${currentTrip.currency} ${currentTrip.budget} for ${currentTrip.num_travelers} traveller(s).`;
      // Only send if no history
      import('../store/tripStore').then(({ useTripStore }) => {
        const msgs = useTripStore.getState().chatMessages;
        if (msgs.length === 0) sendMessage(firstMsg);
      });
    }
  }, [currentTrip]);

  const handleExportPDF = () => {
    window.open(`${API_BASE}/itinerary/${tripId}/export`, '_blank');
  };

  if (!currentTrip) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="shimmer" style={{ width: 200, height: 24, margin: '0 auto 12px' }} />
          <div className="shimmer" style={{ width: 140, height: 16, margin: '0 auto' }} />
        </div>
      </div>
    );
  }

  const start = new Date(currentTrip.start_date);
  const end = new Date(currentTrip.end_date);
  const numDays = Math.ceil((end.getTime() - start.getTime()) / 86400000);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <header style={{
        padding: '14px 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(10,14,26,0.95)',
        backdropFilter: 'blur(20px)',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-ghost" onClick={() => navigate('/')} style={{ padding: '6px 10px' }}>
            <ArrowLeft size={16} />
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, var(--teal), var(--teal-dark))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Plane size={14} color="#0A0E1A" />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1rem' }}>{currentTrip.destination}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                {currentTrip.start_date} → {currentTrip.end_date} · {numDays} days · {currentTrip.currency} {currentTrip.budget}
              </div>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={refresh} style={{ padding: '6px 10px', fontSize: '0.8rem' }}>
            <RefreshCw size={14} />
          </button>
          <button className="btn btn-secondary" onClick={handleExportPDF} style={{ fontSize: '0.8rem', padding: '6px 14px' }}>
            <Download size={14} /> Export PDF
          </button>
        </div>
      </header>

      {/* Main layout: chat left, content right */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '380px 1fr', minHeight: 0 }}>
        {/* Chat Panel */}
        <div style={{ borderRight: '1px solid var(--border)', height: 'calc(100vh - 60px)', position: 'sticky', top: 60 }}>
          <ChatPanel tripId={tripId!} />
        </div>

        {/* Right Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Tabs */}
          <div style={{ padding: '16px 24px 0', borderBottom: '1px solid var(--border)', background: 'rgba(10,14,26,0.5)' }}>
            <div className="tabs" style={{ maxWidth: 480 }}>
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id as any)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
            {isLoading && activeTab === 'itinerary' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[1,2,3].map(i => (
                  <div key={i} className="shimmer" style={{ height: 80, borderRadius: 12 }} />
                ))}
              </div>
            )}
            {!isLoading && (
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                style={{ height: 'auto' }}
              >
                {activeTab === 'dashboard' && <Dashboard />}
                {activeTab === 'itinerary' && <ItineraryView />}
                {activeTab === 'backups' && <BackupOptionsView />}
                {activeTab === 'budget' && <BudgetTracker />}
                {activeTab === 'weather' && <WeatherWidget />}
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
