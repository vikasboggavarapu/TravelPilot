import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { MapPin, Calendar, DollarSign, Users, Heart, ArrowRight, ArrowLeft, Plane } from 'lucide-react';
import { useTripStore } from '../store/tripStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const INTERESTS = [
  { id: 'culture', label: 'Culture & History', emoji: '🏛️' },
  { id: 'food', label: 'Food & Dining', emoji: '🍽️' },
  { id: 'adventure', label: 'Adventure & Sports', emoji: '🎯' },
  { id: 'nightlife', label: 'Nightlife', emoji: '🌙' },
  { id: 'relaxation', label: 'Relaxation & Wellness', emoji: '🧘' },
  { id: 'shopping', label: 'Shopping', emoji: '🛍️' },
  { id: 'nature', label: 'Nature & Parks', emoji: '🌿' },
  { id: 'art', label: 'Art & Museums', emoji: '🎨' },
];

const TRANSPORT_OPTIONS = [
  { id: 'public_transport', label: 'Public Transport', emoji: '🚌' },
  { id: 'taxi', label: 'Taxi / Ride-share', emoji: '🚕' },
  { id: 'walking', label: 'Walking', emoji: '🚶' },
  { id: 'rental_car', label: 'Rental Car', emoji: '🚗' },
];

interface FormData {
  destination: string;
  origin_city: string;
  start_date: string;
  end_date: string;
  budget: string;
  currency: string;
  num_travelers: number;
  interests: string[];
  dietary: string[];
  hotel_stars: number;
  transport_mode: string;
}

export default function PlanTrip() {
  const navigate = useNavigate();
  const { setCurrentTrip } = useTripStore();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState<FormData>({
    destination: '',
    origin_city: '',
    start_date: '',
    end_date: '',
    budget: '',
    currency: localStorage.getItem('travelpilot_currency') || 'INR',
    num_travelers: 1,
    interests: [],
    dietary: [],
    hotel_stars: 3,
    transport_mode: 'public_transport',
  });

  const update = (k: keyof FormData, v: any) => setForm(f => ({ ...f, [k]: v }));

  const toggleInterest = (id: string) => {
    update('interests', form.interests.includes(id)
      ? form.interests.filter(x => x !== id)
      : [...form.interests, id]);
  };

  const canProceed = () => {
    if (step === 1) return form.destination.trim() && form.start_date && form.end_date;
    if (step === 2) return form.budget && parseFloat(form.budget) > 0;
    return true;
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError('');
    try {
      // Create user (simplified — use a fixed guest user)
      let userId = localStorage.getItem('travelpilot_user_id');
      if (!userId) {
        const { data: user } = await axios.post(`${API_BASE}/profile/`, {
          name: 'Traveller',
          currency: form.currency,
          preferences: { interests: form.interests, transport_mode: form.transport_mode, hotel_stars: form.hotel_stars },
        });
        userId = user.user_id;
        localStorage.setItem('travelpilot_user_id', userId!);
      }

      // Create trip
      const { data: trip } = await axios.post(`${API_BASE}/trips`, {
        user_id: userId,
        destination: form.destination,
        origin_city: form.origin_city || null,
        start_date: form.start_date,
        end_date: form.end_date,
        num_travelers: form.num_travelers,
        budget: parseFloat(form.budget),
        currency: form.currency,
        trip_preferences: {
          interests: form.interests,
          dietary: form.dietary,
          hotel_stars: form.hotel_stars,
          transport_mode: form.transport_mode,
        },
      });

      setCurrentTrip(trip);
      navigate(`/trip/${trip.trip_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create trip. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const steps = ['Destination', 'Budget', 'Interests', 'Preferences'];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      {/* Back to home */}
      <button className="btn btn-ghost" onClick={() => navigate('/')}
        style={{ position: 'fixed', top: 20, left: 20, fontSize: '0.85rem' }}>
        <ArrowLeft size={14} /> Home
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass"
        style={{ width: '100%', maxWidth: 560, overflow: 'hidden' }}
      >
        {/* Header */}
        <div style={{ padding: '28px 32px 20px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, var(--teal), var(--teal-dark))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Plane size={15} color="#0A0E1A" />
            </div>
            <span style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem' }}>Plan Your Trip</span>
          </div>

          {/* Step indicator */}
          <div style={{ display: 'flex', gap: 6, marginTop: 16 }}>
            {steps.map((s, i) => (
              <div key={s} style={{ flex: 1 }}>
                <div style={{
                  height: 3, borderRadius: 2,
                  background: i < step ? 'var(--teal)' : i === step - 1 ? 'var(--teal)' : 'rgba(255,255,255,0.1)',
                  transition: 'background 0.3s',
                }} />
                <div style={{ fontSize: '0.65rem', color: i < step ? 'var(--teal)' : 'var(--text-muted)', marginTop: 4, fontWeight: i === step - 1 ? 600 : 400 }}>
                  {s}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step content */}
        <div style={{ padding: '24px 32px' }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              transition={{ duration: 0.2 }}
            >
              {step === 1 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <h2 style={{ fontSize: '1.3rem', marginBottom: 4 }}>Where are you going? 🌍</h2>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>Destination *</label>
                    <input className="input" placeholder="e.g. Paris, France" value={form.destination}
                      onChange={e => update('destination', e.target.value)} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>Flying from (optional)</label>
                    <input className="input" placeholder="e.g. London, UK" value={form.origin_city}
                      onChange={e => update('origin_city', e.target.value)} />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>Check-in *</label>
                      <input className="input" type="date" value={form.start_date}
                        min={new Date().toISOString().split('T')[0]}
                        onChange={e => update('start_date', e.target.value)} />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>Check-out *</label>
                      <input className="input" type="date" value={form.end_date}
                        min={form.start_date || new Date().toISOString().split('T')[0]}
                        onChange={e => update('end_date', e.target.value)} />
                    </div>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>Travellers</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <button className="btn btn-ghost" style={{ padding: '6px 14px' }}
                        onClick={() => update('num_travelers', Math.max(1, form.num_travelers - 1))}>−</button>
                      <span style={{ fontWeight: 700, fontSize: '1.1rem', minWidth: 20, textAlign: 'center' }}>{form.num_travelers}</span>
                      <button className="btn btn-ghost" style={{ padding: '6px 14px' }}
                        onClick={() => update('num_travelers', Math.min(20, form.num_travelers + 1))}>+</button>
                    </div>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <h2 style={{ fontSize: '1.3rem', marginBottom: 4 }}>What's your budget? 💰</h2>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>Total Trip Budget *</label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <select className="input" value={form.currency}
                        onChange={e => {
                          const c = e.target.value;
                          try { localStorage.setItem('travelpilot_currency', c); } catch {}
                          update('currency', c);
                        }} style={{ width: 90 }}>
                        {['INR', 'EUR', 'USD', 'GBP', 'AUD', 'JPY'].map(c => <option key={c}>{c}</option>)}
                      </select>
                      <input className="input" type="number"
                        placeholder={form.currency === 'INR' ? 'e.g. 150000' : form.currency === 'JPY' ? 'e.g. 250000' : 'e.g. 2000'}
                        value={form.budget}
                        onChange={e => update('budget', e.target.value)} style={{ flex: 1 }} />
                    </div>
                  </div>
                  {form.budget && form.start_date && form.end_date && (
                    <div style={{
                      padding: '12px 16px', borderRadius: 8,
                      background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.2)',
                      fontSize: '0.85rem', color: 'var(--teal)',
                    }}>
                      💡 ~{form.currency} {(parseFloat(form.budget) / Math.max(1,
                        Math.ceil((new Date(form.end_date).getTime() - new Date(form.start_date).getTime()) / 86400000)
                      )).toFixed(0)} per day
                    </div>
                  )}
                  <div>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, display: 'block' }}>Hotel Star Rating</label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {[1,2,3,4,5].map(s => (
                        <button key={s} onClick={() => update('hotel_stars', s)}
                          style={{
                            padding: '8px 14px', borderRadius: 8, border: 'none', cursor: 'pointer',
                            background: form.hotel_stars >= s ? 'var(--gold)' : 'rgba(255,255,255,0.05)',
                            color: form.hotel_stars >= s ? '#0A0E1A' : 'var(--text-secondary)',
                            fontWeight: 600, transition: 'var(--transition)',
                          }}>⭐</button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <h2 style={{ fontSize: '1.3rem', marginBottom: 4 }}>What do you love? ❤️</h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>Pick all that apply — we'll plan around your passions.</p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                    {INTERESTS.map(int => (
                      <button key={int.id} onClick={() => toggleInterest(int.id)}
                        style={{
                          padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                          background: form.interests.includes(int.id) ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.04)',
                          border: form.interests.includes(int.id) ? '1px solid rgba(0,212,170,0.4)' : '1px solid var(--border)',
                          color: form.interests.includes(int.id) ? 'var(--teal)' : 'var(--text-secondary)',
                          display: 'flex', alignItems: 'center', gap: 8,
                          fontFamily: 'var(--font-ui)', fontSize: '0.85rem', fontWeight: 500,
                          transition: 'var(--transition)',
                        }}>
                        <span>{int.emoji}</span> {int.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {step === 4 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <h2 style={{ fontSize: '1.3rem', marginBottom: 4 }}>Getting around 🚀</h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {TRANSPORT_OPTIONS.map(t => (
                      <button key={t.id} onClick={() => update('transport_mode', t.id)}
                        style={{
                          padding: '14px 18px', borderRadius: 10, cursor: 'pointer',
                          background: form.transport_mode === t.id ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.04)',
                          border: form.transport_mode === t.id ? '1px solid rgba(0,212,170,0.4)' : '1px solid var(--border)',
                          color: form.transport_mode === t.id ? 'var(--teal)' : 'var(--text-secondary)',
                          display: 'flex', alignItems: 'center', gap: 12,
                          fontFamily: 'var(--font-ui)', fontSize: '0.9rem', fontWeight: 500,
                          transition: 'var(--transition)', textAlign: 'left',
                        }}>
                        <span style={{ fontSize: '1.3rem' }}>{t.emoji}</span> {t.label}
                        {form.transport_mode === t.id && <span style={{ marginLeft: 'auto', fontSize: '0.75rem' }}>✓ Selected</span>}
                      </button>
                    ))}
                  </div>
                  {error && (
                    <div style={{ padding: '10px 14px', background: 'rgba(255,77,109,0.1)', border: '1px solid rgba(255,77,109,0.3)', borderRadius: 8, fontSize: '0.85rem', color: 'var(--danger)' }}>
                      ⚠️ {error}
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div style={{ padding: '16px 32px 24px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button className="btn btn-ghost" onClick={() => setStep(s => s - 1)} disabled={step === 1}
            style={{ visibility: step === 1 ? 'hidden' : 'visible' }}>
            <ArrowLeft size={14} /> Back
          </button>
          {step < 4 ? (
            <button className="btn btn-primary" onClick={() => setStep(s => s + 1)} disabled={!canProceed()}>
              Next <ArrowRight size={14} />
            </button>
          ) : (
            <button className="btn btn-primary" onClick={handleSubmit} disabled={isSubmitting}
              style={{ fontSize: '0.95rem', padding: '12px 28px' }}>
              {isSubmitting ? '✈️ Building your trip...' : '🚀 Plan My Trip!'}
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
