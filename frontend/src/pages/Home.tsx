import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plane, MapPin, Clock, Shield, Sparkles, ArrowRight } from 'lucide-react';

const FEATURES = [
  { icon: '🗓️', title: 'Smart Itinerary', desc: 'Day-by-day plans optimised for your interests & schedule' },
  { icon: '⚡', title: 'Live Adaptation', desc: 'Instant re-planning when cancellations or weather hit' },
  { icon: '💬', title: 'Natural Language', desc: 'Ask anything — from "what\'s close to my hotel?" to "fit in the Louvre?"' },
  { icon: '💰', title: 'Budget Tracking', desc: 'Real-time cost estimates across all categories' },
  { icon: '🌤️', title: 'Weather Aware', desc: 'Forecasts baked into your itinerary with indoor backups' },
  { icon: '🗺️', title: 'Interactive Map', desc: 'Visual route optimisation to minimise travel time' },
];

export default function Home() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Nav */}
      <nav style={{
        padding: '20px 40px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--teal), var(--teal-dark))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Plane size={18} color="#0A0E1A" />
          </div>
          <span style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: 700 }}>TravelPilot</span>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/plan')}>
          Plan a Trip <ArrowRight size={14} />
        </button>
      </nav>

      {/* Hero */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', textAlign: 'center', padding: '80px 24px 60px',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Background glow */}
        <div style={{
          position: 'absolute', top: '20%', left: '50%', transform: 'translateX(-50%)',
          width: 600, height: 600, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
         

          <h1 style={{ marginBottom: 20, lineHeight: 1.1 }}>
            Your AI Travel Guide<br />
            <span style={{
              background: 'linear-gradient(135deg, var(--teal), #00FFCC)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
              Your Dream to Destination
            </span>
          </h1>

          <p style={{ fontSize: '1.1rem', maxWidth: 520, margin: '0 auto 40px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            TravelPilot builds, manages, and adapts your entire trip — handling disruptions,
            answering questions, and keeping your itinerary perfect in real time.
          </p>

          <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
            <motion.button
              className="btn btn-primary"
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/plan')}
              style={{ fontSize: '1rem', padding: '14px 32px' }}
            >
              🌍 Plan My Trip <ArrowRight size={16} />
            </motion.button>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          style={{ display: 'flex', gap: 40, marginTop: 60, flexWrap: 'wrap', justifyContent: 'center' }}
        >
          {[['24/7', 'Available'], ['Real-time', 'Disruption Mgmt']].map(([val, lab]) => (
            <div key={lab} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--teal)' }}>{val}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{lab}</div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Features */}
      <div style={{ padding: '60px 40px', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
        <h2 style={{ textAlign: 'center', marginBottom: 40 }}>Everything you need for a perfect trip</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.07 }}
              className="glass"
              style={{ padding: 24 }}
            >
              <div style={{ fontSize: '2rem', marginBottom: 12 }}>{f.icon}</div>
              <h3 style={{ marginBottom: 8, color: 'var(--text-primary)' }}>{f.title}</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{ textAlign: 'center', padding: '60px 24px', borderTop: '1px solid var(--border)' }}>
        <h2 style={{ marginBottom: 12 }}>Ready to travel smarter?</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 28 }}>Start planning in 2 minutes.</p>
        <button className="btn btn-primary" onClick={() => navigate('/plan')}
          style={{ fontSize: '1rem', padding: '14px 36px' }}>
          Get Started — It's Free ✈️
        </button>
      </div>
    </div>
  );
}
