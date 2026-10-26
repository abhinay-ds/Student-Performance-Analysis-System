"""
Centralized UI Theme and Styling System for Campus Performance Portal.
Academic ERP Visual Language:
- Primary: Deep Navy (#142B4A)
- Accent: Professional Blue (#2563EB)
- Page Background: #F5F7FB
- Cards & Surfaces: #FFFFFF
- Main Text: #1F2937
- Secondary Text: #64748B
- Borders: #E2E8F0
- Success: #16A34A, Warning: #D97706, Error: #DC2626
"""

from typing import Optional, Any
import streamlit as st
import plotly.graph_objects as go

# ============================================================================
# Design Tokens
# ============================================================================
PRIMARY = "#142B4A"         # Deep Navy
PRIMARY_HOVER = "#0F2038"
ACCENT = "#2563EB"          # Professional Blue
ACCENT_HOVER = "#1D4ED8"
SIDEBAR_BG = "#0B1727"      # High-contrast ERP Dark Navy
PAGE_BG = "#F5F7FB"         # Clean Neutral Canvas
CARD_BG = "#FFFFFF"         # Surfaces
TEXT_MAIN = "#1F2937"       # Primary text
TEXT_MUTED = "#64748B"      # Secondary text
BORDER = "#E2E8F0"          # Borders and dividers
SUCCESS = "#16A34A"
WARNING = "#D97706"
ERROR = "#DC2626"
INFO = "#2563EB"

CHART_COLORWAY = [
    "#142B4A",  # Deep Navy
    "#2563EB",  # Accent Blue
    "#16A34A",  # Emerald
    "#D97706",  # Amber
    "#DC2626",  # Crimson
    "#0284C7",  # Sky
]


def inject_global_theme() -> None:
    """Inject global CSS rules to ensure consistent academic ERP styling across all pages."""
    st.markdown(
        """
        <style>
        /* Base typography and background */
        .stApp {
            background-color: #F5F7FB !important;
            color: #1F2937;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        /* Modern Dark Navy ERP Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #0B1727 !important;
            border-right: 1px solid #1E293B !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
        section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
            color: #E2E8F0;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #E2E8F0 !important;
        }

        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
        section[data-testid="stSidebar"] small {
            color: #94A3B8 !important;
        }

        section[data-testid="stSidebar"] hr {
            border-color: #1E293B !important;
        }

        /* Sidebar Navigation Category Labels */
        [data-testid="stSidebarNavSeparator"] {
            color: #64748B !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.6px !important;
            padding-top: 14px !important;
        }

        /* Sidebar Navigation links */
        [data-testid="stSidebarNav"] {
            background-color: transparent !important;
        }

        [data-testid="stSidebarNav"] span, 
        [data-testid="stSidebarNav"] svg {
            color: #94A3B8 !important;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 6px !important;
            padding: 7px 12px !important;
            margin: 2px 0 !important;
            transition: all 0.15s ease-in-out;
        }

        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(255, 255, 255, 0.06) !important;
        }

        [data-testid="stSidebarNav"] a:hover span,
        [data-testid="stSidebarNav"] a:hover svg {
            color: #FFFFFF !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: rgba(37, 99, 235, 0.18) !important;
            border-left: 3px solid #2563EB !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNav"] a[aria-current="page"] svg {
            color: #60A5FA !important;
            font-weight: 600 !important;
        }

        /* Sidebar buttons */
        section[data-testid="stSidebar"] .stButton > button {
            background-color: #16243A !important;
            color: #F1F5F9 !important;
            border: 1px solid #1E293B !important;
            font-weight: 500;
            border-radius: 6px;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background-color: #1E293B !important;
            border-color: #334155 !important;
            color: #FFFFFF !important;
        }

        /* Standardized Metric KPI Cards */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            padding: 14px 18px !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03) !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #64748B !important;
            font-weight: 600 !important;
            font-size: 12px !important;
            letter-spacing: 0.4px;
            text-transform: uppercase;
        }

        div[data-testid="stMetricValue"] {
            color: #142B4A !important;
            font-weight: 700 !important;
            font-size: 24px !important;
            line-height: 1.2;
        }

        /* Button Hierarchy */
        .stButton > button[kind="primary"] {
            background-color: #142B4A !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            padding: 8px 16px !important;
            box-shadow: 0 1px 2px rgba(20, 43, 74, 0.15);
            transition: all 0.15s ease-in-out;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #0F2038 !important;
            box-shadow: 0 2px 4px rgba(20, 43, 74, 0.25);
        }
        .stButton > button[kind="secondary"],
        .stButton > button:not([kind="primary"]) {
            background-color: #FFFFFF;
            color: #1F2937;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            font-weight: 500;
            font-size: 14px;
            padding: 8px 16px;
            transition: all 0.15s ease-in-out;
        }
        .stButton > button[kind="secondary"]:hover,
        .stButton > button:not([kind="primary"]):hover {
            background-color: #F8FAFC;
            border-color: #94A3B8;
        }

        /* Tabs Styling */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 13px !important;
            color: #64748B !important;
            padding: 8px 14px !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #142B4A !important;
            border-bottom-color: #142B4A !important;
        }

        /* Standardized Card Container */
        .saas-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        }

        .saas-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #F1F5F9;
            padding-bottom: 10px;
            margin-bottom: 12px;
        }

        .saas-card-title {
            font-size: 15px;
            font-weight: 600;
            color: #142B4A;
            margin: 0;
        }

        /* Semantic Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            line-height: 1.3;
        }
        .badge-success {
            background-color: #DCFCE7;
            color: #166534;
            border: 1px solid #BBF7D0;
        }
        .badge-warning {
            background-color: #FEF3C7;
            color: #92400E;
            border: 1px solid #FDE68A;
        }
        .badge-error {
            background-color: #FEE2E2;
            color: #991B1B;
            border: 1px solid #FECACA;
        }
        .badge-info {
            background-color: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
        }
        .badge-primary {
            background-color: #EBF1F9;
            color: #142B4A;
            border: 1px solid #CBD8E8;
        }
        .badge-neutral {
            background-color: #F1F5F9;
            color: #475569;
            border: 1px solid #E2E8F0;
        }

        /* Tables and DataFrames */
        [data-testid="stDataFrame"] {
            border: 1px solid #E2E8F0 !important;
            border-radius: 6px !important;
            overflow: hidden !important;
            background-color: #FFFFFF !important;
        }

        /* Section Headings */
        .page-header-container {
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid #E2E8F0;
        }
        .page-title {
            color: #142B4A;
            font-size: 22px;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.3px;
        }
        .page-subtitle {
            color: #64748B;
            font-size: 13px;
            margin: 4px 0 0 0;
        }

        /* Form Controls */
        input[type="text"], input[type="password"], input[type="number"], textarea, .stSelectbox [data-baseweb="select"] {
            border-radius: 6px !important;
            border-color: #CBD5E1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: Optional[str] = None, badge_text: Optional[str] = None, badge_variant: str = "info") -> None:
    """Render a clean, modern academic ERP page header with optional subtitle and status badge."""
    badge_html = f"&nbsp;&nbsp;{render_badge(badge_text, badge_variant)}" if badge_text else ""
    subtitle_html = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="page-header-container">
            <h1 class="page-title">{title}{badge_html}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, variant: str = "info") -> str:
    """Return inline HTML string for a semantic badge."""
    var_class = {
        "success": "badge-success",
        "warning": "badge-warning",
        "error": "badge-error",
        "info": "badge-info",
        "primary": "badge-primary",
        "neutral": "badge-neutral",
    }.get(variant.lower(), "badge-info")
    return f'<span class="badge {var_class}">{text}</span>'


def render_kpi_card(title: str, value: Any, subtitle: Optional[str] = None, delta: Optional[str] = None, delta_color: str = "normal") -> None:
    """Render a standardized Streamlit metric KPI."""
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)


def apply_plotly_theme(fig: Optional[go.Figure]) -> Optional[go.Figure]:
    """
    Standardize a Plotly figure to conform with the Campus Performance Portal
    minimal academic ERP design system.
    """
    if fig is None:
        return None

    fig.update_layout(
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", size=12, color="#1F2937"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CHART_COLORWAY,
        xaxis=dict(
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            linecolor="#E2E8F0",
            tickfont=dict(color="#64748B", size=11),
            title_font=dict(color="#142B4A", size=12, weight="bold"),
        ),
        yaxis=dict(
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            linecolor="#E2E8F0",
            tickfont=dict(color="#64748B", size=11),
            title_font=dict(color="#142B4A", size=12, weight="bold"),
        ),
        legend=dict(
            font=dict(color="#1F2937", size=11),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#E2E8F0",
            borderwidth=1,
        ),
        margin=dict(l=30, r=30, t=45, b=30),
    )
    return fig
