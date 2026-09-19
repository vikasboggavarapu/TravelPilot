import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2, MapPin, RefreshCw, Zap } from 'lucide-react';
import { useTripStore, ChatMessage } from '../store/tripStore';
import { useChat } from '../hooks/useChat';

interface ChatPanelProps { tripId: string; }

const QUICK_QUESTIONS = [
  { text: "What should I do tomorrow morning?", icon: "🌅", label: "Tomorrow Morning" },
  { text: "Can I fit this activity into today's schedule?", icon: "⏱️", label: "Fit Activity" },
  { text: "Which activities are close to my hotel?", icon: "🏨", label: "Close to Hotel" },
  { text: "What happens to my itinerary if this booking is cancelled?", icon: "🛡️", label: "Cancellation & Backups" },
];

export default function ChatPanel({ tripId }: ChatPanelProps) {
  const { chatMessages, isChatLoading } = useTripStore();
  const { sendMessage } = useChat(tripId);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="chat-panel glass" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="chat-header" style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--teal), var(--teal-dark))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Bot size={18} color="#0A0E1A" />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>TravelPilot AI</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <span className="pulse" style={{ width: 6, height: 6 }} />
            Always on for your trip
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        {chatMessages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            style={{ textAlign: 'center', padding: '30px 16px' }}
          >
            <div style={{
              width: 58, height: 58, borderRadius: '50%',
              background: 'var(--teal-glow)', border: '2px solid var(--teal)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 14px',
            }}>
              <Zap size={26} color="var(--teal)" />
            </div>
            <h3 style={{ marginBottom: 6, fontSize: '1.05rem' }}>Ask me anything about your trip!</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
              Select a frequent question or type any question below:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {QUICK_QUESTIONS.map((q) => (
                <button key={q.text} className="btn btn-ghost" style={{ fontSize: '0.8rem', textAlign: 'left', justifyContent: 'flex-start', padding: '8px 12px' }}
                  onClick={() => { sendMessage(q.text); }}>
                  {q.icon} {q.text}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {chatMessages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{ display: 'flex', gap: 10, alignItems: 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}
            >
              <div style={{
                width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, var(--gold), #e09000)'
                  : 'linear-gradient(135deg, var(--teal), var(--teal-dark))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {msg.role === 'user'
                  ? <User size={14} color="#0A0E1A" />
                  : <Bot size={14} color="#0A0E1A" />}
              </div>
              <div style={{
                maxWidth: '80%', padding: '10px 14px',
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, rgba(255,181,71,0.15), rgba(255,181,71,0.08))'
                  : 'rgba(255,255,255,0.05)',
                border: `1px solid ${msg.role === 'user' ? 'rgba(255,181,71,0.2)' : 'var(--border)'}`,
                borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
              }}>
                <MessageContent content={msg.content} />
                {msg.agent_node && (
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <MapPin size={9} /> via {msg.agent_node}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isChatLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <div style={{
              width: 30, height: 30, borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--teal), var(--teal-dark))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Bot size={14} color="#0A0E1A" />
            </div>
            <div style={{
              padding: '10px 16px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border)',
              borderRadius: '4px 16px 16px 16px',
              display: 'flex', gap: 6, alignItems: 'center',
            }}>
              {[0, 1, 2].map(i => (
                <motion.div key={i}
                  style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--teal)' }}
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 0.7, delay: i * 0.15, repeat: Infinity }}
                />
              ))}
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick Prompts Bar */}
      <div style={{
        padding: '8px 12px 6px',
        display: 'flex',
        gap: 6,
        overflowX: 'auto',
        borderTop: '1px solid var(--border)',
        background: 'rgba(255,255,255,0.01)',
      }}>
        {QUICK_QUESTIONS.map(q => (
          <button
            key={q.text}
            className="btn btn-ghost"
            onClick={() => sendMessage(q.text)}
            disabled={isChatLoading}
            style={{
              fontSize: '0.72rem',
              padding: '4px 10px',
              borderRadius: 20,
              border: '1px solid var(--border)',
              background: 'rgba(255,255,255,0.03)',
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
            title={q.text}
          >
            <span>{q.icon}</span> {q.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={{ padding: '8px 12px 12px' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            className="input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask about your trip..."
            disabled={isChatLoading}
            style={{ flex: 1 }}
          />
          <button className="btn btn-primary" onClick={handleSend} disabled={isChatLoading || !input.trim()}
            style={{ padding: '10px 14px', flexShrink: 0 }}>
            {isChatLoading ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageContent({ content }: { content: string }) {
  // Simple markdown-like rendering
  const lines = content.split('\n');
  return (
    <div style={{ fontSize: '0.875rem', lineHeight: 1.7 }}>
      {lines.map((line, i) => {
        if (line.startsWith('**') && line.endsWith('**')) {
          return <div key={i} style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{line.slice(2, -2)}</div>;
        }
        if (line.startsWith('- ') || line.startsWith('• ')) {
          return <div key={i} style={{ paddingLeft: 12, color: 'var(--text-secondary)' }}>• {line.slice(2)}</div>;
        }
        return <div key={i} style={{ color: line ? 'var(--text-secondary)' : undefined }}>{line || <br />}</div>;
      })}
    </div>
  );
}
