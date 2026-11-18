"""Streamlit UI styling helpers, repository cards, and shared rendering utilities."""

from datetime import datetime
import inspect
import os
import textwrap
from typing import Any, Optional, Union
import streamlit as st

from config import get_settings
from database.connection import check_db_health
from database.models import Repository
from database.repository_store import RepositoryStore

LANGUAGE_COLORS: dict[str, str] = {
    "python": "#3572A5",
    "typescript": "#3178C6",
    "javascript": "#F1E05A",
    "rust": "#DEA584",
    "go": "#00ADD8",
    "c++": "#F34B7D",
    "c": "#555555",
    "c#": "#178600",
    "java": "#B07219",
    "php": "#4F5D95",
    "ruby": "#701516",
    "swift": "#F05138",
    "kotlin": "#A97BFF",
    "dart": "#00B4AB",
    "shell": "#89E051",
    "html": "#E34C26",
    "css": "#563D7C",
    "jupyter notebook": "#DA5B0B",
}


def inject_custom_css() -> None:
    """Inject Cinematic Editorial design system CSS."""
    _CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Syne:wght@700;800&display=swap');

/* 1. Neutralize Streamlit stale opacity flicker & jarring double-show effect */
div[data-stale="true"],
.stApp[data-stale="true"],
[data-testid="stSidebar"][data-stale="true"],
[data-testid="stSidebarContent"][data-stale="true"],
[data-testid="stSidebarUserContent"][data-stale="true"],
[data-testid="stMainBlockContainer"][data-stale="true"] {
    opacity: 1 !important;
    filter: none !important;
    transition: none !important;
}

/* Prevent DOM-recreation flicker across reruns */
.stApp,
.stApp [data-testid="stSidebar"],
.stApp [data-testid="stSidebarContent"],
.stApp [data-testid="stSidebarNav"] {
    transition: none !important;
}

/* Subtle, ultra-smooth page fade-in (pure opacity, zero layout shift) */
@keyframes pageFadeIn {
    from { opacity: 0.88; }
    to { opacity: 1; }
}

.stApp [data-testid="stMainBlockContainer"] {
    animation: pageFadeIn 0.18s ease-out !important;
}

/* Global typography & base */
html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background-color: #181818 !important;
    color: #EBDCC4 !important;
}

/* Subtle 3% analog noise overlay */
.stApp::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.035'/%3E%3C/svg%3E");
            pointer-events: none;
            z-index: 999999;
        }

        /* Hide Streamlit Deploy button to prevent accidental clicks */
        .stDeployButton, [data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* Headlines */
        h1, h2, h3, h4 {
            font-family: 'Syne', sans-serif !important;
            text-transform: uppercase !important;
            letter-spacing: -0.01em !important;
            color: #EBDCC4 !important;
        }

/* Minimal Sidebar (Dark Matte Editorial & Design Lab Style) */
        [data-testid="stSidebar"] {
            background-color: #141414 !important;
            border-right: 1px solid #35211A !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: #35211A !important;
        }

        /* Clean Sidebar Layout */
        [data-testid="stSidebarUserContent"] {
            padding-bottom: 12px !important;
        }

        /* Sidebar Navigation Links (Capsule / Pill Style from Reference UI) */
        [data-testid="stSidebarNav"] {
            padding-top: 6px !important;
        }

        [data-testid="stSidebarNav"] ul {
            gap: 2px !important;
            padding: 0 4px !important;
        }

        [data-testid="stSidebarNav"] li {
            margin-bottom: 2px !important;
        }

        [data-testid="stSidebarNav"] li a {
            border-radius: 8px !important;
            padding: 7px 12px !important;
            color: #B6A596 !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            transition: background-color 0.12s ease, color 0.12s ease !important;
            border: 1px solid transparent !important;
            text-decoration: none !important;
            transform: none !important;
        }

        [data-testid="stSidebarNav"] li a:hover {
            background: rgba(220, 159, 133, 0.08) !important;
            color: #EBDCC4 !important;
            border-color: rgba(102, 71, 59, 0.3) !important;
            transform: none !important;
        }

        /* Active Item: Dark Capsule Pill with Coral Border (Like 'Home' in Reference) */
        [data-testid="stSidebarNav"] li a[aria-current="page"] {
            background: #25201D !important;
            color: #EBDCC4 !important;
            font-weight: 600 !important;
            border-color: #DC9F85 !important;
            box-shadow: none !important;
            transform: none !important;
        }

        [data-testid="stSidebarNav"] li a[aria-current="page"] span {
            color: #EBDCC4 !important;
            font-weight: 600 !important;
        }

        /* Native Streamlit page_link in Sidebar matching Design Lab Capsule Spec */
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
            border-radius: 8px !important;
            padding: 7px 12px !important;
            color: #B6A596 !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            transition: background-color 0.12s ease, color 0.12s ease !important;
            border: 1px solid transparent !important;
            text-decoration: none !important;
            background: transparent !important;
            box-shadow: none !important;
            transform: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
            background: rgba(220, 159, 133, 0.08) !important;
            color: #EBDCC4 !important;
            border-color: rgba(102, 71, 59, 0.35) !important;
            transform: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: #25201D !important;
            color: #EBDCC4 !important;
            font-weight: 600 !important;
            border-color: #DC9F85 !important;
        }

        /* Sidebar Bottom Section (Design Lab Minimal Editorial Style) */
        .sidebar-bottom-section {
            position: sticky !important;
            bottom: 0 !important;
            background: #141414 !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 2px !important;
            padding: 10px 0 8px 0 !important;
            margin-top: auto !important;
            font-family: 'General Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            user-select: none !important;
            border-top: 1px solid rgba(53, 33, 26, 0.6) !important;
            box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.6) !important;
            z-index: 10 !important;
        }

        .sidebar-dashed-divider {
            border-top: 1px dashed rgba(182, 165, 150, 0.22) !important;
            margin: 12px 6px 10px 6px !important;
            height: 0 !important;
        }

        .sidebar-nav-row {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            padding: 8px 12px !important;
            border-radius: 8px !important;
            color: #B6A596 !important;
            text-decoration: none !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            line-height: 1 !important;
            letter-spacing: 0.2px !important;
            transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
            border: 1px solid transparent !important;
            background: transparent !important;
            cursor: pointer !important;
            box-sizing: border-box !important;
        }

        .sidebar-nav-row:hover {
            background: rgba(220, 159, 133, 0.08) !important;
            color: #EBDCC4 !important;
            border-color: rgba(102, 71, 59, 0.35) !important;
            transform: translateX(2px) !important;
        }

        .sidebar-nav-left {
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }

        .sidebar-nav-icon {
            width: 18px !important;
            height: 18px !important;
            stroke: currentColor !important;
            fill: none !important;
            stroke-width: 1.8 !important;
            stroke-linecap: round !important;
            stroke-linejoin: round !important;
            flex-shrink: 0 !important;
            transition: stroke 0.18s ease !important;
        }

        .sidebar-nav-row:hover .sidebar-nav-icon {
            stroke: #DC9F85 !important;
        }

        .sidebar-nav-label {
            font-size: 13.5px !important;
            font-weight: 500 !important;
        }

        .sidebar-badge {
            background: rgba(220, 159, 133, 0.16) !important;
            color: #DC9F85 !important;
            border: 1px solid rgba(220, 159, 133, 0.35) !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            padding: 1px 7px !important;
            border-radius: 6px !important;
            line-height: 1.3 !important;
            letter-spacing: 0.3px !important;
        }

        /* Collapsible Telemetry Details */
        details.sidebar-telemetry-expandable {
            border-radius: 8px !important;
            transition: background 0.2s ease !important;
        }

        details.sidebar-telemetry-expandable summary {
            list-style: none !important;
        }

        details.sidebar-telemetry-expandable summary::-webkit-details-marker {
            display: none !important;
        }

        .sidebar-telemetry-card {
            background: #181818 !important;
            border: 1px solid #35211A !important;
            border-radius: 8px !important;
            padding: 10px 12px !important;
            margin: 4px 6px 8px 6px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
        }

        .telemetry-row {
            display: flex !important;
            align-items: center !important;
            gap: 9px !important;
        }

        .telemetry-dot {
            width: 7px !important;
            height: 7px !important;
            border-radius: 50% !important;
            flex-shrink: 0 !important;
        }

        .dot-green {
            background-color: #4ade80 !important;
            box-shadow: 0 0 6px #4ade80 !important;
        }

        .dot-amber {
            background-color: #fbbf24 !important;
            box-shadow: 0 0 6px #fbbf24 !important;
        }

        .dot-red {
            background-color: #f87171 !important;
            box-shadow: 0 0 6px #f87171 !important;
        }

        .telemetry-meta {
            display: flex !important;
            flex-direction: column !important;
            gap: 1px !important;
        }

        .telemetry-title {
            font-size: 11px !important;
            font-weight: 600 !important;
            color: #EBDCC4 !important;
            line-height: 1.2 !important;
        }

        .telemetry-sub {
            font-size: 10px !important;
            color: #B6A596 !important;
            line-height: 1.2 !important;
        }

        .sidebar-footer-brand {
            display: flex !important;
            align-items: center !important;
            gap: 7px !important;
            padding: 12px 10px 4px 10px !important;
            font-size: 11px !important;
            font-weight: 500 !important;
            color: #66473B !important;
            letter-spacing: 0.5px !important;
        }

        .sidebar-status-beacon {
            width: 6px !important;
            height: 6px !important;
            border-radius: 50% !important;
            background-color: #4ade80 !important;
            box-shadow: 0 0 8px #4ade80 !important;
            animation: pulse-beacon 2s infinite ease-in-out !important;
        }

        @keyframes pulse-beacon {
            0%, 100% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }

        /* Card Containers: 4px corners, 1px solid #66473B border, no pill shapes, no box shadows */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1E1C1A !important;
            border: 1px solid #66473B !important;
            border-radius: 4px !important;
            box-shadow: none !important;
            transition: border-color 0.2s ease !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #DC9F85 !important;
        }

        /* Metric Tiles: 4px corners, burnt umber / deep earth borders */
        [data-testid="stMetric"] {
            background-color: #1E1C1A !important;
            border: 1px solid #66473B !important;
            border-radius: 4px !important;
            padding: 10px 14px !important;
            box-shadow: none !important;
        }
        [data-testid="stMetricLabel"] {
            color: #B6A596 !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
        }
        [data-testid="stMetricValue"] {
            color: #EBDCC4 !important;
            font-family: 'Syne', sans-serif !important;
            font-size: 20px !important;
            font-weight: 800 !important;
        }

        /* Action Buttons: Solid #DC9F85, #181818 text, uppercase, bold, 4px corners, custom glow */
        .stButton > button {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 700 !important;
            font-size: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.6px !important;
            border-radius: 4px !important;
            border: 1px solid #66473B !important;
            background-color: #211D1B !important;
            color: #EBDCC4 !important;
            box-shadow: none !important;
            transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
            padding: 7px 16px !important;
        }
        .stButton > button:hover {
            border-color: #DC9F85 !important;
            background-color: #2E211A !important;
            color: #DC9F85 !important;
            box-shadow: 0 0 16px rgba(220, 159, 133, 0.25) !important;
            transform: translateY(-1px) !important;
        }
        .stButton > button:active {
            transform: scale(0.98) !important;
        }

        /* Primary Action Buttons with Coral Glow & Smooth Hover */
        .stButton > button[kind="primary"] {
            background-color: #DC9F85 !important;
            border: 1px solid #DC9F85 !important;
            color: #181818 !important;
            font-weight: 800 !important;
            box-shadow: 0 0 16px rgba(220, 159, 133, 0.3) !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #E5B09A !important;
            border-color: #E5B09A !important;
            color: #181818 !important;
            box-shadow: 0 0 30px rgba(220, 159, 133, 0.7), 0 4px 14px rgba(0, 0, 0, 0.6) !important;
            transform: translateY(-1px) !important;
        }
        .stButton > button[kind="primary"]:active {
            transform: scale(0.97) !important;
        }

        /* Text Inputs & Dropdowns */
        .stTextInput input, .stSelectbox [data-baseweb="select"] {
            background-color: #141312 !important;
            border: 1px solid #66473B !important;
            border-radius: 4px !important;
            color: #EBDCC4 !important;
            font-size: 13px !important;
        }
        .stTextInput input:focus {
            border-color: #DC9F85 !important;
            box-shadow: none !important;
        }

        /* Rectangular Tags (No pill shapes): 4px corners */
        .radar-tag {
            display: inline-block;
            background-color: #261B16;
            color: #B6A596;
            border: 1px solid #4D3328;
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin: 2px 4px 2px 0;
        }

        /* Editorial Hero Typography & Depth */
        .editorial-hero-title {
            font-family: 'Syne', sans-serif !important;
            font-size: clamp(40px, 7.5vw, 88px) !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: -0.025em !important;
            line-height: 0.88 !important;
            color: #EBDCC4 !important;
            position: relative;
            text-shadow: 4px 4px 0px #35211A, 2px 2px 0px #66473B;
            margin: 8px 0 16px 0 !important;
        }

        .editorial-hero-sub {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 17px !important;
            font-weight: 300 !important;
            line-height: 1.6 !important;
            color: #EBDCC4 !important;
            max-width: 580px;
        }

        .editorial-lead-stat {
            font-size: 12px;
            font-weight: 600;
            color: #B6A596;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            margin-top: 12px;
        }

        /* Fixed Persistent Floating Dock (macOS Style Responsive Across ALL Devices) */
        .fixed-dock-container {
            position: fixed !important;
            bottom: max(14px, env(safe-area-inset-bottom, 14px)) !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            z-index: 999999 !important;
            pointer-events: auto !important;
            width: fit-content !important;
            max-width: calc(100vw - 16px) !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            box-sizing: border-box !important;
            padding: 0 4px !important;
            transition: left 0.3s cubic-bezier(0.16, 1, 0.3, 1), bottom 0.25s ease !important;
        }

        /* Desktop Center Alignment with Streamlit Sidebar Expanded */
        @media (min-width: 992px) {
            [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="true"]) .fixed-dock-container,
            [data-testid="stSidebar"][aria-expanded="true"] ~ section.main .fixed-dock-container {
                left: calc(50% + 10.5rem) !important;
            }
        }

        .fixed-dock-panel {
            background: rgba(24, 24, 24, 0.94) !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border: 1px solid #35211A !important;
            box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(102, 71, 59, 0.25) !important;
            border-radius: 18px !important;
            padding: 7px 12px !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            flex-wrap: nowrap !important;
            overflow: visible !important;
        }

        .fixed-dock-panel:hover {
            border-color: #66473B !important;
            box-shadow: 0 20px 48px -8px rgba(0, 0, 0, 0.95), 0 0 20px rgba(220, 159, 133, 0.2) !important;
        }

        .fixed-dock-item {
            position: relative !important;
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            flex-shrink: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 10px !important;
            background: #1E1C1A !important;
            border: 1px solid #35211A !important;
            color: #B6A596 !important;
            text-decoration: none !important;
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
            transform-origin: bottom center !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4) !important;
            box-sizing: border-box !important;
            -webkit-tap-highlight-color: transparent !important;
            user-select: none !important;
        }

        /* Expanded Touch Hit Target for All Devices (Apple 44px HIG compliance) */
        .fixed-dock-item::after {
            content: '' !important;
            position: absolute !important;
            top: -8px !important;
            bottom: -8px !important;
            left: -3px !important;
            right: -3px !important;
            z-index: 10 !important;
            pointer-events: auto !important;
        }

        .fixed-dock-item svg {
            width: 20px !important;
            height: 20px !important;
            transition: all 0.2s ease !important;
            stroke: #B6A596 !important;
            pointer-events: none !important;
            display: block !important;
        }

        /* Active Page Indicator Dot and Highlight */
        .fixed-dock-item.fixed-dock-active {
            background: #2A1F1A !important;
            border-color: #DC9F85 !important;
            color: #EBDCC4 !important;
            box-shadow: 0 0 14px rgba(220, 159, 133, 0.35) !important;
        }
        .fixed-dock-item.fixed-dock-active svg {
            stroke: #DC9F85 !important;
        }
        .fixed-dock-item.fixed-dock-active .fixed-dock-dot {
            display: block !important;
        }

        .fixed-dock-dot {
            display: none;
            position: absolute !important;
            bottom: 2px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 4px !important;
            height: 4px !important;
            border-radius: 50% !important;
            background-color: #DC9F85 !important;
            box-shadow: 0 0 6px #DC9F85 !important;
            pointer-events: none !important;
        }

        /* Fluid macOS Bell-Curve Magnification Wave (Pointer Devices / Desktops / Laptops) */
        @media (hover: hover) and (pointer: fine) {
            /* Center Hovered Item */
            .fixed-dock-item:hover {
                transform: translateY(-9px) scale(1.36) !important;
                background: #2A1F1A !important;
                border-color: #DC9F85 !important;
                color: #EBDCC4 !important;
                box-shadow: 0 14px 28px -4px rgba(0, 0, 0, 0.8), 0 0 18px rgba(220, 159, 133, 0.45) !important;
                z-index: 50 !important;
            }
            .fixed-dock-item:hover svg {
                stroke: #DC9F85 !important;
            }

            /* 1st Neighbor to the right */
            .fixed-dock-item:hover + .fixed-dock-item {
                transform: translateY(-5px) scale(1.18) !important;
                border-color: #66473B !important;
                background: #241A16 !important;
                z-index: 40 !important;
            }
            .fixed-dock-item:hover + .fixed-dock-item svg {
                stroke: #EBDCC4 !important;
            }

            /* 2nd Neighbor to the right */
            .fixed-dock-item:hover + .fixed-dock-item + .fixed-dock-item {
                transform: translateY(-2px) scale(1.08) !important;
                border-color: #4A332A !important;
                z-index: 30 !important;
            }

            /* 1st Neighbor to the left */
            .fixed-dock-item:has(+ .fixed-dock-item:hover) {
                transform: translateY(-5px) scale(1.18) !important;
                border-color: #66473B !important;
                background: #241A16 !important;
                z-index: 40 !important;
            }
            .fixed-dock-item:has(+ .fixed-dock-item:hover) svg {
                stroke: #EBDCC4 !important;
            }

            /* 2nd Neighbor to the left */
            .fixed-dock-item:has(+ .fixed-dock-item + .fixed-dock-item:hover) {
                transform: translateY(-2px) scale(1.08) !important;
                border-color: #4A332A !important;
                z-index: 30 !important;
            }

            /* Elegant Editorial Tooltip Balloon */
            .fixed-dock-item::before {
                content: attr(data-tooltip) !important;
                position: absolute !important;
                top: -38px !important;
                left: 50% !important;
                transform: translateX(-50%) translateY(4px) !important;
                background: #141414 !important;
                border: 1px solid #66473B !important;
                color: #EBDCC4 !important;
                font-size: 10px !important;
                font-weight: 700 !important;
                letter-spacing: 0.6px !important;
                text-transform: uppercase !important;
                padding: 4px 9px !important;
                border-radius: 4px !important;
                white-space: nowrap !important;
                opacity: 0 !important;
                pointer-events: none !important;
                box-shadow: 0 6px 14px rgba(0, 0, 0, 0.75) !important;
                transition: opacity 0.15s ease, transform 0.15s ease !important;
                z-index: 99999999 !important;
            }

            .fixed-dock-item:hover::before {
                opacity: 1 !important;
                transform: translateX(-50%) translateY(0) !important;
            }
        }

        /* Tactile Instant Feedback on Active Tap / Click (Haptic Feel) */
        .fixed-dock-item:active {
            transform: scale(0.88) !important;
            background-color: #35211A !important;
            border-color: #DC9F85 !important;
            box-shadow: 0 0 12px rgba(220, 159, 133, 0.5) !important;
            transition: transform 0.06s ease, background 0.06s ease !important;
        }

        /* Responsive Breakpoints for Tablet (768px - 1024px) */
        @media (max-width: 1024px) {
            .fixed-dock-panel {
                gap: 5px !important;
                padding: 6px 10px !important;
            }
            .fixed-dock-item {
                width: 38px !important;
                height: 38px !important;
                min-width: 38px !important;
                border-radius: 8px !important;
            }
            .fixed-dock-item svg {
                width: 18px !important;
                height: 18px !important;
            }
        }

        /* Responsive Breakpoints for Large Mobile / Phablets (480px - 767px) */
        @media (max-width: 767px) {
            .fixed-dock-container {
                bottom: max(10px, env(safe-area-inset-bottom, 10px)) !important;
                max-width: 100vw !important;
                padding: 0 6px !important;
            }
            .fixed-dock-panel {
                gap: 4px !important;
                padding: 4px 8px !important;
                border-radius: 14px !important;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.9) !important;
            }
            .fixed-dock-item {
                width: 31px !important;
                height: 31px !important;
                min-width: 31px !important;
                border-radius: 6px !important;
            }
            .fixed-dock-item svg {
                width: 15px !important;
                height: 15px !important;
            }
            .fixed-dock-item::before {
                display: none !important;
            }
        }

        /* Responsive Breakpoints for Standard Smartphones (375px - 479px, e.g. iPhone 12/13/14/15/16, Galaxy S21/S22/S23) */
        @media (max-width: 479px) {
            .fixed-dock-container {
                bottom: max(8px, env(safe-area-inset-bottom, 8px)) !important;
                padding: 0 4px !important;
            }
            .fixed-dock-panel {
                gap: 3px !important;
                padding: 3px 5px !important;
                border-radius: 12px !important;
            }
            .fixed-dock-item {
                width: 27px !important;
                height: 27px !important;
                min-width: 27px !important;
                border-radius: 5px !important;
            }
            .fixed-dock-item svg {
                width: 14px !important;
                height: 14px !important;
            }
            .fixed-dock-dot {
                width: 3px !important;
                height: 3px !important;
                bottom: 1.5px !important;
            }
        }

        /* Responsive Breakpoints for Compact Smartphones & Foldables (< 375px, e.g. Galaxy Z Fold cover, iPhone SE) */
        @media (max-width: 374px) {
            .fixed-dock-panel {
                gap: 2px !important;
                padding: 3px 4px !important;
                border-radius: 10px !important;
            }
            .fixed-dock-item {
                width: 23px !important;
                height: 23px !important;
                min-width: 23px !important;
                border-radius: 4px !important;
            }
            .fixed-dock-item svg {
                width: 12px !important;
                height: 12px !important;
            }
            .fixed-dock-dot {
                width: 2.5px !important;
                height: 2.5px !important;
                bottom: 1px !important;
            }
        }

        /* Page Bottom Margin so dock never obscures content on ANY device */
        .main .block-container, [data-testid="stMainBlockContainer"] {
            padding-bottom: 110px !important;
        }

        @media (max-width: 768px) {
            .main .block-container, [data-testid="stMainBlockContainer"] {
                padding-bottom: 85px !important;
            }
        }

        /* Language indicator */
        .lang-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 2px;
            margin-right: 5px;
            vertical-align: middle;
        }

        /* Status circle indicator */
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #DC9F85;
            margin-right: 6px;
            vertical-align: middle;
        }

        /* Dividers */
        hr {
            border-color: #35211A !important;
        }

        /* Editorial Tabs */
        [data-baseweb="tab-list"] {
            border-bottom: 1px solid #35211A !important;
        }
        [data-baseweb="tab"] {
            color: #B6A596 !important;
            font-weight: 600 !important;
            font-size: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        [aria-selected="true"] {
            color: #DC9F85 !important;
            border-bottom: 2px solid #DC9F85 !important;
        }

        /* Sleek earth scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #181818;
        }
        ::-webkit-scrollbar-thumb {
            background: #35211A;
            border-radius: 2px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #66473B;
        }
</style>"""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_page_header(
    title: str,
    subtitle: str,
    icon: Optional[str] = None,
) -> None:
    """Render a standardized Cinematic Editorial page header."""
    inject_custom_css()
    icon_str = f"{icon} " if icon else ""

    st.markdown(
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        '<span style="font-size: 11px; font-weight: 700; color: #B6A596; letter-spacing: 1.5px; text-transform: uppercase;">RADAR — PROTOCOL 01</span>'
        '<span style="font-size: 11px; font-weight: 600; color: #DC9F85; letter-spacing: 0.8px;"><span class="status-dot"></span>LIVE TELEMETRY</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">'
        f'<div style="width: 24px; height: 2px; background-color: #DC9F85;"></div>'
        f'<span style="font-size: 11px; font-weight: 700; color: #B6A596; letter-spacing: 1.2px; text-transform: uppercase;">INTELLIGENCE ENGINE</span>'
        f'</div>'
        f'<h1 style="font-family: \'Syne\', sans-serif; font-size: 32px; font-weight: 800; text-transform: uppercase; color: #EBDCC4; margin: 0; line-height: 1.05;">'
        f'{icon_str}{title}'
        f'</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<p style="color: #B6A596; font-size: 13px; margin-top: 6px; margin-bottom: 16px;">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color: #35211A; margin-top: 0; margin-bottom: 24px;">', unsafe_allow_html=True)


def render_editorial_hero() -> None:
    """Render the cinematic editorial landing hero section."""
    inject_custom_css()
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 2px; padding-bottom: 16px;">
            <div style="color: #B6A596; font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;">
                SD—PROTOCOL 01
            </div>
            <div style="flex-grow: 1; height: 1px; background-color: #35211A; margin: 0 24px;"></div>
            <div style="color: #DC9F85; font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; display: flex; align-items: center; gap: 8px;">
                <span class="status-dot"></span>INVITE ONLY &bull; LIVE TELEMETRY
            </div>
        </div>

        <div style="margin-top: 4px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <div style="width: 24px; height: 2px; background-color: #DC9F85;"></div>
                <span style="color: #B6A596; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;">EARLY ACCESS &bull; TECH INTELLIGENCE</span>
            </div>
            <h1 class="editorial-hero-title">
                OPENSOURCE RADAR
            </h1>
        </div>

        <hr style="border: none; border-top: 1px solid #35211A; margin: 16px 0 24px 0;" />
        """,
        unsafe_allow_html=True,
    )


def get_current_page_name() -> str:
    """Detect current page name from execution stack for active dock highlighting."""
    try:
        for frame in inspect.stack():
            fname = frame.filename.replace("\\", "/")
            if "/pages/" in fname:
                base = os.path.basename(fname)
                name = os.path.splitext(base)[0]
                parts = name.split("_", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    return parts[1]
                return name
            if fname.endswith("/app.py"):
                return "Overview"
    except Exception:
        pass
    return ""


def render_floating_dock(current_page: str = "") -> None:
    """Render the persistent macOS-inspired floating magnification dock locked at the bottom of the viewport."""
    active_page = current_page or get_current_page_name()

    items = [
        ("Overview", "/Overview", "01 Overview", '<path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>'),
        ("Discover", "/Discover", "02 Discover", '<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>'),
        ("Trending", "/Trending", "03 Trending", '<path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>'),
        ("Hidden_Gems", "/Hidden_Gems", "04 Hidden Gems", '<path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>'),
        ("AI_Agents", "/AI_Agents", "05 AI Agents", '<path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>'),
        ("Trading_FinTech", "/Trading_FinTech", "06 FinTech", '<path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>'),
        ("Repository_Analyzer", "/Repository_Analyzer", "07 Analyzer", '<path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>'),
        ("Compare", "/Compare", "08 Compare", '<path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>'),
        ("Content_Studio", "/Content_Studio", "09 Studio", '<path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>'),
        ("Saved_Projects", "/Saved_Projects", "10 Saved", '<path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>'),
        ("Settings", "/Settings", "12 Settings", '<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>'),
    ]

    links_html = []
    for page_key, url, tooltip, path_d in items:
        is_active = (active_page.lower() == page_key.lower()) or (active_page == "" and page_key == "Overview")
        active_cls = " fixed-dock-active" if is_active else ""
        link_str = f"""<a href="{url}" target="_self" class="fixed-dock-item{active_cls}" data-tooltip="{tooltip}"><svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">{path_d}</svg><span class="fixed-dock-dot"></span></a>"""
        links_html.append(link_str)

    items_markup = "\n            ".join(links_html)

    dock_html = textwrap.dedent(
        f"""
        <div class="fixed-dock-container">
          <div class="fixed-dock-panel" role="toolbar" aria-label="OpenSource Radar Persistent Dock">
            {items_markup}
          </div>
        </div>
        """
    ).strip()
    st.markdown(dock_html, unsafe_allow_html=True)


def render_magnification_dock() -> None:
    """Backward compatibility alias for render_floating_dock."""
    render_floating_dock()


def render_sidebar_status(current_page: str = "") -> None:
    """Render sleek editorial bottom section matching reference UI with notifications & telemetry."""
    inject_custom_css()
    render_floating_dock(current_page=current_page)
    with st.sidebar:
        settings = get_settings()
        
        # GitHub Status
        if settings.has_github_token:
            gh_status = f"Authenticated ({settings.masked_github_token})"
            gh_ok = True
        else:
            gh_status = "Public (60 req/hr)"
            gh_ok = False

        # Database Status
        db_health = check_db_health()
        if db_health.get("connected"):
            db_status = "Connected (SQLite WAL)"
            db_ok = True
        else:
            db_status = "Disconnected"
            db_ok = False

        # AI Status
        if settings.AI_PROVIDER == "openai":
            if settings.has_openai_credentials:
                ai_status = f"OpenAI ({settings.OPENAI_MODEL})"
                ai_ok = True
            else:
                ai_status = "OpenAI (Fallback Mode)"
                ai_ok = False
        elif settings.AI_PROVIDER == "gemini":
            if settings.has_gemini_credentials:
                ai_status = f"Gemini ({settings.GEMINI_MODEL})"
                ai_ok = True
            else:
                ai_status = "Gemini (Fallback Mode)"
                ai_ok = False
        else:
            ai_status = "Offline / Deterministic"
            ai_ok = True

        active_count = sum([1 for ok in (gh_ok, db_ok, ai_ok) if ok])
        badge_count = f"{active_count}"

        gh_dot = "dot-green" if gh_ok else "dot-amber"
        db_dot = "dot-green" if db_ok else "dot-red"
        ai_dot = "dot-green" if ai_ok else "dot-amber"

        sidebar_html = textwrap.dedent(
            f"""
            <div class="sidebar-bottom-section">
                <div class="sidebar-dashed-divider"></div>
                <a href="/Overview" target="_self" class="sidebar-nav-row" title="Resources &amp; Radar Architecture">
                    <div class="sidebar-nav-left">
                        <svg class="sidebar-nav-icon" viewBox="0 0 24 24">
                            <path d="M4 4h5v16H4z M15 4h5v16h-5z M4 9h5 M15 9h5 M4 15h5 M15 15h5"/>
                        </svg>
                        <span class="sidebar-nav-label">Resources</span>
                    </div>
                </a>
                <details class="sidebar-telemetry-expandable">
                    <summary class="sidebar-nav-row" title="Click to view live system notifications and telemetry">
                        <div class="sidebar-nav-left">
                            <svg class="sidebar-nav-icon" viewBox="0 0 24 24">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                            </svg>
                            <span class="sidebar-nav-label">Notifications</span>
                        </div>
                        <span class="sidebar-badge">{badge_count}</span>
                    </summary>
                    <div class="sidebar-telemetry-card">
                        <div class="telemetry-row">
                            <span class="telemetry-dot {gh_dot}"></span>
                            <div class="telemetry-meta">
                                <span class="telemetry-title">GitHub API</span>
                                <span class="telemetry-sub">{gh_status}</span>
                            </div>
                        </div>
                        <div class="telemetry-row">
                            <span class="telemetry-dot {db_dot}"></span>
                            <div class="telemetry-meta">
                                <span class="telemetry-title">SQLite Database</span>
                                <span class="telemetry-sub">{db_status}</span>
                            </div>
                        </div>
                        <div class="telemetry-row">
                            <span class="telemetry-dot {ai_dot}"></span>
                            <div class="telemetry-meta">
                                <span class="telemetry-title">AI Engine</span>
                                <span class="telemetry-sub">{ai_status}</span>
                            </div>
                        </div>
                    </div>
                </details>
                <div class="sidebar-dashed-divider"></div>
                <a href="https://github.com" target="_blank" class="sidebar-nav-row" title="Support &amp; Community">
                    <div class="sidebar-nav-left">
                        <svg class="sidebar-nav-icon" viewBox="0 0 24 24">
                            <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
                            <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
                        </svg>
                        <span class="sidebar-nav-label">Support</span>
                    </div>
                </a>
                <a href="/Settings" target="_self" class="sidebar-nav-row" title="Configuration &amp; API Keys">
                    <div class="sidebar-nav-left">
                        <svg class="sidebar-nav-icon" viewBox="0 0 24 24">
                            <path d="M12 2l7.5 4.33v8.66L12 22l-7.5-4.33V6.33L12 2z"/>
                            <circle cx="12" cy="12" r="3.2"/>
                        </svg>
                        <span class="sidebar-nav-label">Setting</span>
                    </div>
                </a>
                <div class="sidebar-footer-brand">
                    <span class="sidebar-status-beacon"></span>
                    <span>OpenSource Radar v1.0.0</span>
                </div>
            </div>
            """
        ).strip()
        st.markdown(sidebar_html, unsafe_allow_html=True)


def render_repository_card(repo: Union[dict[str, Any], Repository], key_prefix: str = "") -> None:
    """
    Render a standardized SaaS-style repository card with metadata, metrics, and actions.
    Supports both normalized dictionaries and SQLAlchemy Repository model instances.
    """
    if isinstance(repo, Repository):
        github_id = repo.github_id
        db_id = repo.id
        full_name = repo.full_name
        html_url = repo.html_url
        description = repo.description or "No description provided."
        stars = repo.stars
        forks = repo.forks
        language = repo.primary_language or "N/A"
        category_name = repo.category.display_name if repo.category else "General"
        pushed_at = repo.pushed_at_github
        topics = repo.topics or []
    else:
        github_id = repo.get("github_id")
        full_name = repo.get("full_name")
        html_url = repo.get("html_url")
        description = repo.get("description") or "No description provided."
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        language = repo.get("primary_language") or "N/A"
        category_name = repo.get("subcategory") or repo.get("category_key", "General").title()
        pushed_at = repo.get("pushed_at_github")
        topics = repo.get("topics", [])
        # Look up DB ID
        db_repo = RepositoryStore.get_by_github_id(github_id) if github_id else None
        db_id = db_repo.id if db_repo else None

    # Format date
    if isinstance(pushed_at, datetime):
        pushed_str = pushed_at.strftime("%Y-%m-%d")
    elif isinstance(pushed_at, str):
        pushed_str = pushed_at[:10]
    else:
        pushed_str = "N/A"

    is_bookmarked = RepositoryStore.is_saved(db_id) if db_id else False

    # Language dot color
    lang_color = LANGUAGE_COLORS.get((language or "").lower(), "#8B949E")

    with st.container(border=True):
        col_main, col_stats = st.columns([4, 1.2])

        with col_main:
            st.markdown(f"#### [{full_name}]({html_url})")
            st.write(description)
            
            # Badges / metadata
            lang_html = f'<span class="lang-dot" style="background-color: {lang_color};"></span><b>{language}</b>'
            st.markdown(
                f"🏷️ <b>Category</b>: {category_name} &nbsp;|&nbsp; "
                f"{lang_html} &nbsp;|&nbsp; "
                f"📅 <b>Pushed</b>: {pushed_str}",
                unsafe_allow_html=True,
            )
            if topics:
                tags_html = " ".join([f'<span class="radar-tag">{t}</span>' for t in topics[:6]])
                st.markdown(tags_html, unsafe_allow_html=True)

        with col_stats:
            st.metric("Stars", f"{stars:,}")
            st.metric("Forks", f"{forks:,}")

            b_col1, b_col2 = st.columns(2)
            with b_col1:
                unique_key = f"{key_prefix}_{github_id}"
                if is_bookmarked:
                    if st.button("🔖 Saved", key=f"unsave_{unique_key}", help="Click to remove bookmark"):
                        if db_id:
                            RepositoryStore.unsave_repository(db_id)
                            st.rerun()
                else:
                    if st.button("☆ Save", key=f"save_{unique_key}", help="Bookmark repository"):
                        # Ensure repo is in DB
                        if not db_id and isinstance(repo, dict):
                            saved_obj = RepositoryStore.upsert_repository(repo)
                            db_id = saved_obj.id
                        if db_id:
                            RepositoryStore.save_repository(db_id)
                            st.rerun()

            with b_col2:
                if st.button("🔬 Analyze  →", key=f"ana_{unique_key}", help="Open in Repository Analyzer", type="primary"):
                    st.session_state["selected_repo"] = full_name
                    st.switch_page("pages/07_Repository_Analyzer.py")
