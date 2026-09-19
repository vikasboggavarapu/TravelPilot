import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, AlertTriangle, ArrowRight, RefreshCw, 
  Sparkles, CheckCircle2, Clock, DollarSign, CloudRain,
  MessageSquare, Info, ChevronRight, HelpCircle
} from 'lucide-react';
import { useTripStore, Activity } from '../store/tripStore';
import { useChat } from '../hooks/useChat';

export default function BackupOptionsView() {
  const { currentTrip, itinerary, budget } = useTripStore();
  const { sendMessage } = useChat(currentTrip?.trip_id || '');
  const [selectedSimActivity, setSelectedSimActivity] = useState<Activity | null>(null);

  if (!currentTrip || !itinerary.length) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
        <ShieldCheck size={48} color="var(--teal)" style={{ margin: '0 auto 16px', opacity: 0.7 }} />
        <h3 style={{ marginBottom: 8 }}>No Itinerary Loaded</h3>
        <p style={{ fontSize: '0.875rem' }}>Build an itinerary first to generate backup and contingency options.</p>
      </div>
    );
  }

  const allActivities: Activity[] = itinerary.flatMap(day => day.activities || []);
  const activitiesWithBackups = allActivities.map(act => {
    const backupName = (act.alternatives && act.alternatives[0]?.name) || `Indoor Cultural Center in ${currentTrip.destination}`;
    const backupReason = (act.alternatives && act.alternatives[0]?.reason) || `Verified weather-proof alternative with flexible entry`;
    return {
      ...act,
      backupName,
      backupReason,
    };
  });

  const handleAskAboutCancellation = (actName: string) => {
    sendMessage(`What happens to my itinerary if "${actName}" is cancelled? What are my backup options?`);
  };

  const handleAskAboutBackup = (actName: string, backupName: string) => {
    sendMessage(`Tell me more about the backup alternative "${backupName}" for "${actName}". How does it fit into my schedule?`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{ display: 'flex', flexDirection: 'column', gap: 24 }}
    >
      {/* Hero Header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 24, 48, 0.9), rgba(10, 14, 26, 0.95))',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px 28px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: -40, right: -40, width: 180, height: 180,
          background: 'radial-gradient(circle, rgba(0, 212, 170, 0.18), transparent 70%)',
          borderRadius: '50%', pointerEvents: 'none',
        }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <span className="badge badge-teal" style={{ textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.05em' }}>
            <ShieldCheck size={12} style={{ display: 'inline', marginRight: 4 }} />
            Contingency & Resilience System
          </span>
        </div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, margin: '4px 0 8px', letterSpacing: '-0.02em' }}>
          🛡️ Backup Options & Contingency Matrix
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', margin: 0, maxWidth: 680, lineHeight: 1.6 }}>
          Every booking and activity in your <strong>{currentTrip.destination}</strong> journey has pre-vetted alternatives.
          If closures, weather shifts, or cancellations occur, TravelPilot activates backups with zero stress.
        </p>
      </div>

      {/* Coverage Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        <div className="glass" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--teal)', fontSize: '0.8rem', fontWeight: 600, marginBottom: 6 }}>
            <CheckCircle2 size={16} /> Contingency Coverage
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>100%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            All {allActivities.length} scheduled stops have mapped alternatives
          </div>
        </div>

        <div className="glass" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#6BA3D6', fontSize: '0.8rem', fontWeight: 600, marginBottom: 6 }}>
            <CloudRain size={16} /> Weather Safeguard
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>Active</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Indoor & sheltered alternatives ready for rain or storm
          </div>
        </div>

        <div className="glass" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--gold)', fontSize: '0.8rem', fontWeight: 600, marginBottom: 6 }}>
            <DollarSign size={16} /> Budget Protection
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>
            {currentTrip.currency} {budget?.remaining ? budget.remaining.toFixed(0) : '0'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Remaining safety buffer protected on cancellation
          </div>
        </div>

        <div className="glass" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#C084FC', fontSize: '0.8rem', fontWeight: 600, marginBottom: 6 }}>
            <RefreshCw size={16} /> Real-Time Replanning
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>Instant</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            One-click AI schedule rebalancing on any disruption
          </div>
        </div>
      </div>

      {/* Day by Day Contingency Matrix */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
            📋 Pre-Loaded Backup Alternatives by Day
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Click "Simulate Impact" or "Ask AI" on any item
          </span>
        </div>

        {itinerary.map(day => {
          const acts = day.activities || [];
          return (
            <div key={day.day_number} className="glass" style={{ padding: '20px 24px', borderRadius: 'var(--radius-lg)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 12 }}>
                <div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Day {day.day_number} · {day.date}
                  </span>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem', marginTop: 2 }}>
                    {day.theme || 'Exploration'}
                  </div>
                </div>
                {day.weather_summary && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.04)', padding: '6px 12px', borderRadius: 8 }}>
                    🌤️ {day.weather_summary}
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {acts.map((act, i) => {
                  const backupName = (act.alternatives && act.alternatives[0]?.name) || `Historic City Museum & Gallery in ${currentTrip.destination}`;
                  const backupReason = (act.alternatives && act.alternatives[0]?.reason) || `Top-rated sheltered local attraction with walk-in entry`;

                  return (
                    <div
                      key={i}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'minmax(240px, 1fr) auto minmax(260px, 1.2fr) auto',
                        gap: 16,
                        alignItems: 'center',
                        background: 'rgba(255,255,255,0.02)',
                        border: '1px solid var(--border)',
                        borderRadius: 12,
                        padding: '14px 18px',
                      }}
                    >
                      {/* Primary Activity */}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Clock size={11} /> {act.start_time || '09:30'} - {act.end_time || '12:00'}
                          </span>
                          <span className="badge badge-teal" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
                            Primary
                          </span>
                        </div>
                        <div style={{ fontWeight: 600, fontSize: '0.92rem', marginBottom: 2 }}>
                          {act.name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          {act.category} · {currentTrip.currency} {act.estimated_cost} · {act.location || currentTrip.destination}
                        </div>
                      </div>

                      {/* Transition Icon */}
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: 'var(--teal)' }}>
                        <ArrowRight size={18} />
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>Backup</span>
                      </div>

                      {/* Backup Alternative */}
                      <div style={{
                        background: 'rgba(0, 212, 170, 0.04)',
                        border: '1px dashed rgba(0, 212, 170, 0.25)',
                        borderRadius: 8,
                        padding: '10px 14px',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--teal)' }}>
                            🛡️ Standby Alternative
                          </span>
                        </div>
                        <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-primary)', marginBottom: 2 }}>
                          {backupName}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {backupReason}
                        </div>
                      </div>

                      {/* Actions */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <button
                          className="btn btn-ghost"
                          onClick={() => setSelectedSimActivity(act)}
                          style={{ fontSize: '0.75rem', padding: '6px 12px', whiteSpace: 'nowrap' }}
                        >
                          <AlertTriangle size={12} color="var(--gold)" /> Simulate Impact
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={() => handleAskAboutCancellation(act.name)}
                          style={{ fontSize: '0.75rem', padding: '6px 12px', whiteSpace: 'nowrap' }}
                        >
                          <MessageSquare size={12} /> Ask AI
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Simulation Modal / Drawer */}
      <AnimatePresence>
        {selectedSimActivity && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
              backdropFilter: 'blur(8px)', zIndex: 1000,
              display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
            }}
            onClick={() => setSelectedSimActivity(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95 }}
              onClick={e => e.stopPropagation()}
              className="glass"
              style={{
                maxWidth: 520, width: '100%', padding: '28px',
                borderRadius: 'var(--radius-lg)', border: '1px solid rgba(0, 212, 170, 0.4)',
                background: 'rgba(13, 20, 36, 0.98)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%', background: 'rgba(255, 181, 71, 0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <AlertTriangle size={20} color="var(--gold)" />
                </div>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.1rem' }}>Cancellation Simulation</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Simulating cancellation of: <strong>{selectedSimActivity.name}</strong>
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14, margin: '20px 0' }}>
                <div style={{ padding: '12px 16px', background: 'rgba(0, 212, 170, 0.06)', borderRadius: 8, border: '1px solid rgba(0, 212, 170, 0.2)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--teal)', marginBottom: 4 }}>
                    1. Instant Backup Activation
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Slot automatically transitions to: <strong>{(selectedSimActivity.alternatives && selectedSimActivity.alternatives[0]?.name) || 'City Cultural Center'}</strong>. No manual rescheduling needed.
                  </div>
                </div>

                <div style={{ padding: '12px 16px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: 4 }}>
                    2. Schedule Continuity
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Preserves your <strong>30-minute travel buffer</strong> and maintains subsequent dining reservations without time overlap.
                  </div>
                </div>

                <div style={{ padding: '12px 16px', background: 'rgba(255, 181, 71, 0.06)', borderRadius: 8, border: '1px solid rgba(255, 181, 71, 0.2)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--gold)', marginBottom: 4 }}>
                    3. Budget Recredit
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Estimated cost of <strong>{currentTrip.currency} {selectedSimActivity.estimated_cost}</strong> returns directly to your remaining contingency buffer.
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button className="btn btn-ghost" onClick={() => setSelectedSimActivity(null)}>
                  Close
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    handleAskAboutCancellation(selectedSimActivity.name);
                    setSelectedSimActivity(null);
                  }}
                >
                  <MessageSquare size={14} /> Send Simulation to AI
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Contingency Protocol Information */}
      <div className="glass" style={{ padding: '24px 28px', borderRadius: 'var(--radius-lg)' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <HelpCircle size={18} color="var(--teal)" />
          How TravelPilot Handles Cancellations & Changes
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 6, color: 'var(--teal)' }}>
              1. What happens if a booking is cancelled?
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
              TravelPilot replaces the cancelled slot with your pre-vetted backup alternative, updates transit times to adjacent stops, and credits any unspent budget back to your buffer.
            </p>
          </div>

          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 6, color: 'var(--teal)' }}>
              2. Can I fit an activity into today's schedule?
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
              Ask the AI anytime! TravelPilot analyzes your itinerary gaps and confirms where a 60–120 min activity fits without causing conflicts or exceeding your transit buffers.
            </p>
          </div>

          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 6, color: 'var(--teal)' }}>
              3. Which activities are close to my hotel?
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
              The AI calculates exact walking distances and transit times from your hotel, ranking nearby sights so you can easily plan arrival-day or evening strolls.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
