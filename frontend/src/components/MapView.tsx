import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useTripStore } from '../store/tripStore';

// Fix default marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom coloured icons by category
const makeIcon = (color: string, emoji: string) => L.divIcon({
  className: '',
  html: `<div style="
    width: 36px; height: 36px; border-radius: 50% 50% 50% 0;
    background: ${color}; transform: rotate(-45deg);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 3px 14px rgba(0,0,0,0.4);
    border: 2px solid rgba(255,255,255,0.3);
  "><span style="transform:rotate(45deg); font-size:16px">${emoji}</span></div>`,
  iconSize: [36, 36],
  iconAnchor: [18, 36],
  popupAnchor: [0, -38],
});

const CATEGORY_ICONS: Record<string, { color: string; emoji: string }> = {
  landmark: { color: '#00D4AA', emoji: '🏛️' },
  food: { color: '#FFB547', emoji: '🍽️' },
  restaurant: { color: '#FFB547', emoji: '🍽️' },
  museum: { color: '#9B8FFF', emoji: '🎨' },
  adventure: { color: '#FF6B6B', emoji: '🎯' },
  hotel: { color: '#4ECDC4', emoji: '🏨' },
  transport: { color: '#6C757D', emoji: '🚌' },
  shopping: { color: '#FF9FF3', emoji: '🛍️' },
  nature: { color: '#7FB069', emoji: '🌿' },
  nightlife: { color: '#C084FC', emoji: '🌙' },
  general: { color: '#8899BB', emoji: '📍' },
};

export default function MapView() {
  const { itinerary, selectedDay } = useTripStore();
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  // Collect all geo-tagged activities
  const allActivities = (selectedDay
    ? itinerary.filter(d => d.day_number === selectedDay)
    : itinerary
  ).flatMap(day =>
    (day.activities || [])
      .filter(a => a.latitude && a.longitude)
      .map(a => ({ ...a, day_number: day.day_number, day_theme: day.theme }))
  );

  const positions: [number, number][] = allActivities.map(a => [a.latitude!, a.longitude!]);
  const defaultCenter: [number, number] = positions[0] ?? [48.8566, 2.3522]; // fallback: Paris

  // Initialize and update Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Create map instance if not existing
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        zoomControl: false,
      }).setView(defaultCenter, 12);

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
      }).addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      const layerGroup = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
      layerGroupRef.current = layerGroup;
    }

    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    // Clear previous markers / polylines
    layerGroup.clearLayers();

    // Draw route polyline
    if (positions.length > 1) {
      L.polyline(positions, {
        color: '#00D4AA',
        weight: 2,
        opacity: 0.5,
        dashArray: '6 8',
      }).addTo(layerGroup);
    }

    // Add activity markers
    allActivities.forEach(act => {
      const cfg = CATEGORY_ICONS[act.category?.toLowerCase()] || CATEGORY_ICONS.general;
      const icon = makeIcon(cfg.color, cfg.emoji);
      const marker = L.marker([act.latitude!, act.longitude!], { icon });

      const popupContent = `
        <div style="font-family: Inter, sans-serif; min-width: 180px; color: #0A0E1A; padding: 4px;">
          <div style="font-weight: 700; margin-bottom: 4px; font-size: 0.95rem;">
            ${cfg.emoji} ${act.name}
          </div>
          <div style="font-size: 0.8rem; color: #555; margin-bottom: 4px;">
            Day ${act.day_number} — ${act.day_theme || 'Exploring'}
          </div>
          ${act.start_time ? `<div style="font-size: 0.8rem; color: #333;">🕐 ${act.start_time}–${act.end_time || ''}</div>` : ''}
          ${act.location ? `<div style="font-size: 0.75rem; color: #666; margin-top: 2px;">📍 ${act.location}</div>` : ''}
          <div style="font-size: 0.8rem; font-weight: 600; color: #00A885; margin-top: 4px;">
            ~$${act.estimated_cost?.toFixed(0) || 0}
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
      marker.addTo(layerGroup);
    });

    // Auto-fit bounds
    if (positions.length > 0) {
      const bounds = L.latLngBounds(positions);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [allActivities.length, selectedDay]);

  // Clean up map instance on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        layerGroupRef.current = null;
      }
    };
  }, []);

  if (!allActivities.length) {
    return (
      <div style={{
        height: '100%', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 12,
      }}>
        <div style={{ fontSize: 48 }}>🗺️</div>
        <h3>No map data yet</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'center' }}>
          Map pins will appear once your itinerary is generated<br />with location coordinates.
        </p>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden', position: 'relative' }}>
      {/* Legend */}
      <div style={{
        position: 'absolute', top: 12, left: 12, zIndex: 1000,
        background: 'rgba(10,14,26,0.9)', backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 10, padding: '8px 12px',
        display: 'flex', flexDirection: 'column', gap: 4,
      }}>
        {Object.entries(CATEGORY_ICONS).slice(0, 5).map(([cat, cfg]) => (
          <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem' }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: cfg.color }} />
            <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{cat}</span>
          </div>
        ))}
      </div>

      {/* Map DOM container */}
      <div
        ref={mapContainerRef}
        style={{ height: '100%', width: '100%', background: '#0A0E1A' }}
      />
    </div>
  );
}
