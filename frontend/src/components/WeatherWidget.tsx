import React from 'react';
import { motion } from 'framer-motion';
import { useTripStore } from '../store/tripStore';
import { Droplets, Wind, Thermometer, CloudRain, Sun, Cloud, CloudSnow, Zap } from 'lucide-react';

const CONDITION_CONFIG: Record<string, { icon: React.ComponentType<any>; color: string; emoji: string }> = {
  Clear: { icon: Sun, color: '#FFB547', emoji: '☀️' },
  Clouds: { icon: Cloud, color: '#8899BB', emoji: '⛅' },
  Rain: { icon: CloudRain, color: '#6BA3D6', emoji: '🌧️' },
  Drizzle: { icon: CloudRain, color: '#8BB4D6', emoji: '🌦️' },
  Snow: { icon: CloudSnow, color: '#B0C8E0', emoji: '❄️' },
  Thunderstorm: { icon: Zap, color: '#FFB547', emoji: '⛈️' },
  Extreme: { icon: Zap, color: '#FF4D6D', emoji: '🚨' },
};

export default function WeatherWidget() {
  const { itinerary } = useTripStore();

  const weatherDays = itinerary
    .map(d => ({ ...d.weather_data, date: d.date, day_number: d.day_number, theme: d.theme, summary: d.weather_summary }))
    .filter(d => d.condition || d.summary);

  if (!weatherDays.length) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🌤️</div>
        <h3 style={{ marginBottom: 8 }}>Weather unavailable</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Weather data will appear after trip planning.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '4px 2px' }}>
      <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 4 }}>
        {weatherDays.map((d, i) => (
          <WeatherCard key={i} day={d} index={i} />
        ))}
      </div>
      <DisruptionAlerts days={weatherDays} />
    </div>
  );
}

function WeatherCard({ day, index }: { day: any; index: number }) {
  const cfg = CONDITION_CONFIG[day.condition] || CONDITION_CONFIG.Clouds;
  const WeatherIcon = cfg.icon;
  const isRisk = day.is_disruption_risk || (day.precipitation_pct || 0) > 60;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="glass"
      style={{
        minWidth: 130, padding: '16px 14px', textAlign: 'center',
        border: isRisk ? '1px solid rgba(255,181,71,0.35)' : '1px solid var(--border)',
        background: isRisk ? 'rgba(255,181,71,0.05)' : 'var(--glass-bg)',
        position: 'relative', overflow: 'hidden',
      }}
    >
      {isRisk && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0,
          height: 3, background: 'linear-gradient(90deg, var(--gold), transparent)',
        }} />
      )}
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>
        Day {day.day_number}
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 12, fontWeight: 500 }}>
        {day.date}
      </div>
      <div style={{ fontSize: '2rem', marginBottom: 8 }}>{cfg.emoji}</div>
      {day.temp_high && (
        <div style={{ marginBottom: 6 }}>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: cfg.color }}>
            {day.temp_high}°
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            /{day.temp_low}°C
          </div>
        </div>
      )}
      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: 8 }}>
        {day.condition || day.summary}
      </div>
      {day.precipitation_pct !== undefined && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, fontSize: '0.72rem', color: '#6BA3D6' }}>
          <Droplets size={10} />
          {day.precipitation_pct}%
        </div>
      )}
    </motion.div>
  );
}

function DisruptionAlerts({ days }: { days: any[] }) {
  const riskDays = days.filter(d => d.is_disruption_risk || (d.precipitation_pct || 0) > 60);
  if (!riskDays.length) {
    return (
      <div className="glass" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ fontSize: '1.5rem' }}>✅</div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--teal)' }}>Great weather ahead!</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>No significant weather disruptions expected.</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <h3 style={{ fontSize: '0.9rem' }}>⚠️ Weather Alerts</h3>
      {riskDays.map((d, i) => (
        <div key={i} className="glass" style={{
          padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12,
          border: '1px solid rgba(255,181,71,0.25)',
          background: 'rgba(255,181,71,0.05)',
        }}>
          <div style={{ fontSize: '1.5rem' }}>🌧️</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--gold)' }}>
              Day {d.day_number} ({d.date}) — {d.condition}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              {d.precipitation_pct}% chance of rain. Consider indoor alternatives.
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
