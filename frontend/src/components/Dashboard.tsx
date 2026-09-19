import React from 'react';
import { motion } from 'framer-motion';
import { 
  Calendar, MapPin, DollarSign, Clock, ShieldCheck, 
  Download, AlertTriangle, CheckCircle2, Navigation, Compass,
  Sparkles, Coffee, Utensils, Bed, Camera
} from 'lucide-react';
import { useTripStore, Activity } from '../store/tripStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const { currentTrip, itinerary, budget, setActiveTab } = useTripStore();

  if (!currentTrip) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
        No trip loaded.
      </div>
    );
  }

  const allActivities: Activity[] = itinerary.flatMap(day => day.activities || []);
  const totalActivities = allActivities.length;
  const bookedActivities = allActivities.filter(a => a.status === 'confirmed').length;
  const atRiskActivities = allActivities.filter(a => a.status === 'at_risk');

  const start = new Date(currentTrip.start_date);
  const end = new Date(currentTrip.end_date);
  const numDays = Math.max(1, Math.ceil((end.getTime() - start.getTime()) / 86400000));

  const handleExportPDF = () => {
    window.open(`${API_BASE}/itinerary/${currentTrip.trip_id}/export`, '_blank');
  };

  const getCategoryIcon = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'food': return <Utensils size={14} color="#00D4AA" />;
      case 'dinner': return <Utensils size={14} color="#FFB547" />;
      case 'hotel': return <Bed size={14} color="#60A5FA" />;
      case 'culture': return <Camera size={14} color="#C084FC" />;
      default: return <Compass size={14} color="#00D4AA" />;
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{ display: 'flex', flexDirection: 'column', gap: 24 }}
    >
      {/* Hero Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 24, 48, 0.9), rgba(10, 14, 26, 0.95))',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '28px 32px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: -50, right: -50, width: 220, height: 220,
          background: 'radial-gradient(circle, rgba(0,212,170,0.15), transparent 70%)',
          borderRadius: '50%', pointerEvents: 'none',
        }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span className="badge badge-teal" style={{ textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.05em' }}>
                Trip Master Dashboard
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                ID: {currentTrip.trip_id.slice(0, 8)}...
              </span>
            </div>
            <h1 style={{ fontSize: '1.85rem', fontWeight: 800, margin: '4px 0 8px', letterSpacing: '-0.02em' }}>
              {currentTrip.destination}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 16, margin: 0 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Calendar size={15} color="var(--teal)" /> {currentTrip.start_date} → {currentTrip.end_date}
              </span>
              <span>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Clock size={15} color="var(--teal)" /> {numDays} Days
              </span>
              <span>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <DollarSign size={15} color="var(--teal)" /> {currentTrip.currency} {currentTrip.budget.toLocaleString()}
              </span>
            </p>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button className="btn btn-secondary" onClick={() => setActiveTab('backups')} style={{ fontSize: '0.85rem' }}>
              <ShieldCheck size={15} color="var(--teal)" /> Backup Options
            </button>
            <button className="btn btn-primary" onClick={handleExportPDF} style={{ fontSize: '0.85rem' }}>
              <Download size={15} /> Download PDF Itinerary
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 16 }}>
        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>
            TOTAL ACTIVITIES
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            {totalActivities}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--teal)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
            <CheckCircle2 size={13} /> {bookedActivities} scheduled
          </div>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>
            ESTIMATED SPEND
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--gold)' }}>
            {currentTrip.currency} {budget?.total_estimated ? budget.total_estimated.toLocaleString() : '0'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Remaining: {currentTrip.currency} {budget?.remaining ? budget.remaining.toLocaleString() : currentTrip.budget.toLocaleString()}
          </div>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>
            DISRUPTION MONITOR
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: atRiskActivities.length > 0 ? 'var(--coral)' : 'var(--teal)' }}>
            {atRiskActivities.length === 0 ? 'Normal' : `${atRiskActivities.length} Alert`}
          </div>
          <div style={{ fontSize: '0.75rem', color: atRiskActivities.length > 0 ? 'var(--coral)' : 'var(--teal)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
            {atRiskActivities.length === 0 ? <ShieldCheck size={13} /> : <AlertTriangle size={13} />}
            {atRiskActivities.length === 0 ? 'All schedules clear' : 'Alternative options ready'}
          </div>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>
            AI AGENT STATUS
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--teal)' }}>
            Active
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
            <Sparkles size={13} color="var(--teal)" /> Ready to re-route on demand
          </div>
        </div>
      </div>

      {/* Days Summary List */}
      <div>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Calendar size={18} color="var(--teal)" /> Itinerary Highlights & Schedule
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {itinerary.map(day => (
            <div 
              key={day.day_id || day.day_number}
              className="card"
              style={{ padding: 20, cursor: 'pointer', transition: 'transform 0.2s' }}
              onClick={() => setActiveTab('itinerary')}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    background: 'rgba(0,212,170,0.12)', border: '1px solid rgba(0,212,170,0.3)',
                    color: 'var(--teal)', fontWeight: 700, fontSize: '0.85rem',
                    padding: '4px 10px', borderRadius: 8,
                  }}>
                    Day {day.day_number}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                      {day.theme || `Exploring ${currentTrip.destination}`}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {day.date} {day.weather_summary ? `• ${day.weather_summary}` : ''}
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--gold)' }}>
                    ~{currentTrip.currency} {day.estimated_cost?.toFixed(0) || 0}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {day.activities?.length || 0} stops
                  </div>
                </div>
              </div>

              {/* Activity mini-timeline preview */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {day.activities?.slice(0, 4).map((act, i) => (
                  <div 
                    key={i}
                    style={{
                      background: 'rgba(255,255,255,0.03)',
                      border: '1px solid var(--border)',
                      borderRadius: 6,
                      padding: '5px 10px',
                      fontSize: '0.78rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    {getCategoryIcon(act.category)}
                    <span style={{ fontWeight: 500 }}>{act.name}</span>
                    {act.start_time && (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                        {act.start_time}
                      </span>
                    )}
                  </div>
                ))}
                {(day.activities?.length || 0) > 4 && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', alignSelf: 'center', paddingLeft: 4 }}>
                    +{day.activities.length - 4} more
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
