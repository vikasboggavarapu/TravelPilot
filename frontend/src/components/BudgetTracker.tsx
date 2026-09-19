import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useTripStore } from '../store/tripStore';
import { TrendingUp, TrendingDown, Wallet } from 'lucide-react';

const COLOURS = ['#00D4AA', '#FFB547', '#9B8FFF', '#FF6B6B'];
const LABELS = ['Accommodation', 'Transport', 'Food', 'Activities'];

export default function BudgetTracker() {
  const { budget, itinerary } = useTripStore();

  if (!budget) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>💰</div>
        <h3 style={{ marginBottom: 8 }}>Budget not calculated yet</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Plan your trip to see budget breakdown.
        </p>
      </div>
    );
  }

  const pieData = [
    { name: 'Accommodation', value: budget.spent_accommodation },
    { name: 'Transport', value: budget.spent_transport },
    { name: 'Food', value: budget.spent_food },
    { name: 'Activities', value: budget.spent_activities },
  ].filter(d => d.value > 0);

  const pctUsed = budget.total_budget > 0
    ? Math.min((budget.total_estimated / budget.total_budget) * 100, 100)
    : 0;

  const isOverBudget = budget.remaining < 0;

  // Daily bar data
  const dailyData = itinerary.map(d => ({
    name: `D${d.day_number}`,
    cost: d.estimated_cost,
    theme: d.theme,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, padding: '4px 2px' }}>
      {/* Overview cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <StatCard
          label="Total Budget"
          value={`${budget.currency} ${budget.total_budget.toFixed(0)}`}
          sub="Your travel budget"
          icon={<Wallet size={18} />}
          color="var(--teal)"
        />
        <StatCard
          label={isOverBudget ? 'Over Budget' : 'Remaining'}
          value={`${budget.currency} ${Math.abs(budget.remaining).toFixed(0)}`}
          sub={isOverBudget ? 'Reduce activities' : 'Available to spend'}
          icon={isOverBudget ? <TrendingDown size={18} /> : <TrendingUp size={18} />}
          color={isOverBudget ? 'var(--danger)' : 'var(--teal)'}
        />
      </div>

      {/* Budget usage bar */}
      <div className="glass" style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Budget Used</span>
          <span style={{ color: isOverBudget ? 'var(--danger)' : 'var(--teal)', fontWeight: 600 }}>
            {pctUsed.toFixed(0)}%
          </span>
        </div>
        <div style={{ height: 10, background: 'rgba(255,255,255,0.08)', borderRadius: 5, overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${pctUsed}%`,
            background: isOverBudget
              ? 'linear-gradient(90deg, var(--danger), #FF6B6B)'
              : 'linear-gradient(90deg, var(--teal), var(--teal-dark))',
            borderRadius: 5,
            transition: 'width 0.8s ease',
          }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>Estimated: {budget.currency} {budget.total_estimated.toFixed(0)}</span>
          <span>Budget: {budget.currency} {budget.total_budget.toFixed(0)}</span>
        </div>
      </div>

      {/* Pie chart */}
      {pieData.length > 0 && (
        <div className="glass" style={{ padding: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: '0.95rem' }}>Spending Breakdown</h3>
          <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
            <ResponsiveContainer width={160} height={160}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={72}
                  paddingAngle={3} dataKey="value">
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLOURS[i % COLOURS.length]} stroke="transparent" />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => [`${budget.currency} ${v.toFixed(0)}`, '']}
                  contentStyle={{ background: 'var(--navy-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {pieData.map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: COLOURS[i % COLOURS.length], flexShrink: 0 }} />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.name}</span>
                  </div>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                    {budget.currency} {item.value.toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Daily bar chart */}
      {dailyData.length > 0 && (
        <div className="glass" style={{ padding: 20 }}>
          <h3 style={{ marginBottom: 16, fontSize: '0.95rem' }}>Daily Spend</h3>
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={dailyData} barSize={24}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} axisLine={false} tickLine={false}
                tickFormatter={(v) => `${budget.currency} ${v}`} width={45} />
              <Tooltip
                formatter={(v: number) => [`${budget.currency} ${v.toFixed(0)}`, 'Cost']}
                contentStyle={{ background: 'var(--navy-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
                cursor={{ fill: 'rgba(0,212,170,0.05)' }}
              />
              <Bar dataKey="cost" fill="url(#barGrad)" radius={[4, 4, 0, 0]} />
              <defs>
                <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00D4AA" />
                  <stop offset="100%" stopColor="#00A885" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, sub, icon, color }: {
  label: string; value: string; sub: string; icon: React.ReactNode; color: string;
}) {
  return (
    <div className="glass" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <div style={{ color, opacity: 0.8 }}>{icon}</div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
      </div>
      <div style={{ fontSize: '1.4rem', fontWeight: 700, color, marginBottom: 2 }}>{value}</div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{sub}</div>
    </div>
  );
}
