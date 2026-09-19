import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, MapPin, DollarSign, ChevronDown, ChevronUp, ExternalLink, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { useTripStore, ItineraryDay, Activity } from '../store/tripStore';

const CATEGORY_ICONS: Record<string, string> = {
  landmark: '🏛️', food: '🍽️', restaurant: '🍽️', museum: '🏛️',
  adventure: '🎯', culture: '🎭', shopping: '🛍️', transport: '🚌',
  hotel: '🏨', nature: '🌿', nightlife: '🌙', cafe: '☕', bar: '🍸',
  beach: '🏖️', sport: '⚽', entertainment: '🎬', general: '📍',
};

const STATUS_CONFIG = {
  confirmed: { label: 'Confirmed', icon: CheckCircle, color: 'var(--teal)', bg: 'rgba(0,212,170,0.1)' },
  at_risk: { label: 'At Risk', icon: AlertTriangle, color: 'var(--gold)', bg: 'rgba(255,181,71,0.1)' },
  cancelled: { label: 'Cancelled', icon: XCircle, color: 'var(--danger)', bg: 'rgba(255,77,109,0.1)' },
  alternative: { label: 'Alternative', icon: CheckCircle, color: '#9B8FFF', bg: 'rgba(155,143,255,0.1)' },
};

export default function ItineraryView() {
  const { itinerary, selectedDay, setSelectedDay, currentTrip, budget } = useTripStore();
  const [expandedAct, setExpandedAct] = useState<string | null>(null);
  const currency = currentTrip?.currency || budget?.currency || 'INR';

  if (!itinerary.length) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🗺️</div>
        <h3 style={{ marginBottom: 8 }}>No itinerary yet</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Chat with TravelPilot to plan your trip!
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '4px 2px' }}>
      {itinerary.map((day) => (
        <DayCard
          key={day.day_id || day.day_number}
          day={day}
          currency={currency}
          isSelected={selectedDay === day.day_number}
          onSelect={() => setSelectedDay(selectedDay === day.day_number ? null : day.day_number)}
          expandedAct={expandedAct}
          setExpandedAct={setExpandedAct}
        />
      ))}
    </div>
  );
}

function DayCard({ day, currency, isSelected, onSelect, expandedAct, setExpandedAct }: {
  day: ItineraryDay; currency: string; isSelected: boolean; onSelect: () => void;
  expandedAct: string | null; setExpandedAct: (id: string | null) => void;
}) {
  const weather = day.weather_data;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass"
      style={{ overflow: 'hidden', cursor: 'pointer', border: isSelected ? '1px solid var(--teal)' : '1px solid var(--border)' }}
    >
      {/* Day Header */}
      <div onClick={onSelect} style={{
        padding: '16px 20px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: isSelected ? 'rgba(0,212,170,0.05)' : 'transparent',
        transition: 'var(--transition)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--teal), var(--teal-dark))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 700, fontSize: '1rem', color: 'var(--navy)', flexShrink: 0,
          }}>
            {day.day_number}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '1rem' }}>{day.theme || `Day ${day.day_number}`}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              {day.date}
              {day.weather_summary && <span style={{ marginLeft: 8 }}>• {day.weather_summary}</span>}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Est. Cost</div>
            <div style={{ color: 'var(--gold)', fontWeight: 600, fontSize: '0.9rem' }}>
              {currency} {day.estimated_cost?.toFixed(0)}
            </div>
          </div>
          {isSelected ? <ChevronUp size={16} color="var(--teal)" /> : <ChevronDown size={16} color="var(--text-secondary)" />}
        </div>
      </div>

      {/* Activities */}
      <AnimatePresence>
        {isSelected && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '0 20px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {day.activities.map((act, i) => (
                <ActivityCard
                  key={`${act.name}-${i}`}
                  activity={act}
                  currency={currency}
                  isExpanded={expandedAct === `${day.day_number}-${i}`}
                  onToggle={() => setExpandedAct(expandedAct === `${day.day_number}-${i}` ? null : `${day.day_number}-${i}`)}
                />
              ))}
              {day.notes && (
                <div style={{
                  marginTop: 4, padding: '10px 14px',
                  background: 'rgba(255,181,71,0.08)',
                  border: '1px solid rgba(255,181,71,0.2)',
                  borderRadius: 8, fontSize: '0.8rem', color: 'var(--gold)',
                }}>
                  📝 {day.notes}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Preview strip when collapsed */}
      {!isSelected && (
        <div style={{
          padding: '0 20px 14px',
          display: 'flex', gap: 8, flexWrap: 'wrap',
        }}>
          {day.activities.slice(0, 4).map((act, i) => (
            <span key={i} style={{
              fontSize: '0.75rem', padding: '3px 8px', borderRadius: 6,
              background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
            }}>
              {CATEGORY_ICONS[act.category] || '📍'} {act.name}
            </span>
          ))}
          {day.activities.length > 4 && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
              +{day.activities.length - 4} more
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
}

function ActivityCard({ activity, currency, isExpanded, onToggle }: {
  activity: Activity; currency: string; isExpanded: boolean; onToggle: () => void;
}) {
  const status = STATUS_CONFIG[activity.status] || STATUS_CONFIG.confirmed;
  const StatusIcon = status.icon;
  const icon = CATEGORY_ICONS[activity.category] || '📍';

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      overflow: 'hidden',
      transition: 'var(--transition)',
    }}>
      <div onClick={onToggle} style={{
        padding: '12px 14px',
        display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer',
      }}>
        {/* Time bar */}
        {activity.start_time && (
          <div style={{
            width: 3, height: 36, borderRadius: 2,
            background: status.color, flexShrink: 0,
          }} />
        )}
        <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{icon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 500, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6 }}>
            {activity.name}
            {activity.booking_required && (
              <span style={{ fontSize: '0.65rem', padding: '1px 6px', borderRadius: 4,
                background: 'rgba(155,143,255,0.15)', color: '#9B8FFF', border: '1px solid rgba(155,143,255,0.3)' }}>
                Book
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', gap: 8, marginTop: 2, flexWrap: 'wrap' }}>
            {activity.start_time && <span><Clock size={10} style={{ verticalAlign: 'middle' }} /> {activity.start_time}–{activity.end_time}</span>}
            {activity.location && <span><MapPin size={10} style={{ verticalAlign: 'middle' }} /> {activity.location}</span>}
          </div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ color: 'var(--gold)', fontSize: '0.85rem', fontWeight: 600 }}>{currency} {activity.estimated_cost?.toFixed(0)}</div>
          <div style={{
            fontSize: '0.65rem', padding: '2px 6px', borderRadius: 4,
            background: status.bg, color: status.color, marginTop: 2,
            display: 'flex', alignItems: 'center', gap: 3,
          }}>
            <StatusIcon size={9} /> {status.label}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              padding: '0 14px 12px',
              borderTop: '1px solid var(--border)',
              paddingTop: 10,
              display: 'flex', flexDirection: 'column', gap: 6,
            }}>
              {activity.description && (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{activity.description}</p>
              )}
              {activity.tips && (
                <div style={{ fontSize: '0.8rem', color: 'var(--gold)', padding: '6px 10px',
                  background: 'rgba(255,181,71,0.08)', borderRadius: 6 }}>
                  💡 {activity.tips}
                </div>
              )}
              {activity.booking_url && (
                <a href={activity.booking_url} target="_blank" rel="noreferrer"
                  className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px', width: 'fit-content' }}>
                  <ExternalLink size={12} /> Book Now
                </a>
              )}
              {activity.travel_to_next && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: 6, alignItems: 'center' }}>
                  🚌 {activity.travel_to_next.duration_minutes} min travel to next stop
                  ({activity.travel_to_next.distance_km} km)
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
