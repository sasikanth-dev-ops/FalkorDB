"""Custom modern dark luxury CSS styling for the AI Career Mentor dashboard."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-primary: #0a0d14;
    --bg-card: rgba(18, 24, 38, 0.7);
    --bg-card-hover: rgba(26, 34, 52, 0.85);
    --border-color: rgba(99, 102, 241, 0.18);
    --border-focus: rgba(99, 102, 241, 0.45);
    --accent-primary: #6366f1;
    --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

code, pre, .stCodeBlock {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Background gradient styling */
.stApp {
    background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.06) 0%, transparent 40%),
                #0b0f19;
    color: var(--text-primary);
}

/* Glassmorphic card styling */
.glass-card {
    background: var(--bg-card);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    border-color: var(--border-focus);
    transform: translateY(-2px);
    box-shadow: 0 20px 30px -10px rgba(99, 102, 241, 0.15);
}

/* Hero Badge */
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.9rem;
    border-radius: 9999px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #a5b4fc;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

/* Gradient Header */
.gradient-title {
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
}

.gradient-title-accent {
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Skill pills */
.pill {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
    letter-spacing: 0.01em;
}

.pill-matched {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
}

.pill-missing {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
}

.pill-category {
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.pill-platform {
    background: rgba(6, 182, 212, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(6, 182, 212, 0.3);
}

/* Metric card styling */
.metric-box {
    background: rgba(18, 24, 38, 0.6);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}

.metric-num {
    font-size: 1.85rem;
    font-weight: 800;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-lbl {
    font-size: 0.78rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
}

/* Streamlit Tab Customization */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(15, 23, 42, 0.6);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid rgba(99, 102, 241, 0.15);
}

.stTabs [data-baseweb="tab"] {
    height: 42px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 8px;
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.88rem;
    padding: 0 16px;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(99, 102, 241, 0.2) !important;
    color: #ffffff !important;
    border: 1px solid rgba(99, 102, 241, 0.35);
}

/* Chat container aesthetic */
.chat-agent-bubble {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px 16px 16px 4px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chat-user-bubble {
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.3) 0%, rgba(147, 51, 234, 0.3) 100%);
    border: 1px solid rgba(147, 51, 234, 0.4);
    border-radius: 16px 16px 4px 16px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Memory update banner */
.memory-pill-alert {
    background: linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%);
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin: 0.75rem 0;
    font-size: 0.85rem;
    color: #6ee7b7;
}
</style>
"""
