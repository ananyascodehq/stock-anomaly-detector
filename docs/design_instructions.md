# UI/UX DESIGN SPECIFICATION — STOCK ANOMALY DETECTOR (v2)

## 0. PURPOSE

This document defines the **exact UI/UX requirements** for the Stock Anomaly Detector dashboard.

Goals:

* Zero ambiguity in implementation
* No stylistic improvisation
* Fully deterministic layout and behavior
* Optimized for **decision-making speed (<5 seconds)**

This is a **monitoring system**, NOT a marketing interface.

---

## 1. GLOBAL DESIGN SYSTEM

### 1.1 Theme

* Mode: **Dark only**
* Background: `#0B0F14`
* Card background: `#11161D`
* Border: `rgba(255,255,255,0.05)`

### 1.2 Typography

* Font: Inter (fallback: system-ui)
* Headings: Semi-bold (600)
* Body: Regular (400)

| Element       | Size                                    |
| ------------- | --------------------------------------- |
| Main Title    | 28px                                    |
| Section Title | 14px (uppercase, letter-spacing 0.08em) |
| Body          | 13px                                    |
| Small         | 11px                                    |

---

### 1.3 Color System

| Purpose               | Color   |
| --------------------- | ------- |
| Primary text          | #E6EDF3 |
| Secondary text        | #9DA7B3 |
| Accent (neutral)      | #4A90E2 |
| Low severity          | #2ECC71 |
| Medium severity       | #F5A623 |
| High severity         | #FF5A5F |
| Critical UI highlight | #FF7A7A |

---

### 1.4 Spacing System

* Base unit: **8px**
* Card padding: 16px
* Section gap: 24px
* Internal gap: 12px

---

## 2. LAYOUT STRUCTURE

### 2.1 Grid

* Layout: 3-column grid
* Sidebar: fixed width (240px)
* Main content: flexible

```
[Sidebar] | [Main Content Area]
```

---

## 3. SIDEBAR

### Components:

* Logo + title
* Navigation items:

  * Dashboard (active)
  * Alerts
  * History
  * Settings
* CTA button: “Inject Anomaly”

### Rules:

* Active item:

  * Background: subtle highlight
  * Left indicator bar (2px)
* Hover:

  * Slight brightness increase only

---

## 4. TOP BAR

### Elements:

* Ticker selector (AAPL, SPY, TSLA)
* Live status icon
* Refresh icon
* User avatar

### Rules:

* Active ticker:

  * Underline highlight
* No dropdown animation delays

---

## 5. MAIN CONTENT

---

## 5.1 PRICE CHART PANEL

### Structure:

* Title: “PRICE FEED VS ANOMALIES”
* Price display (large)
* Volatility indicator
* Time filter buttons: [1m, 5m, 15m, 1H]
* LIVE badge

### Chart Requirements:

#### Line:

* Smooth curve (spline)
* Color: soft blue

#### Anomalies:

* Single anomaly → red dot
* Consecutive anomalies → vertical shaded region

#### Volume:

* Must be shown as bars at bottom
* Low opacity (20%)

#### Interaction:

* Hover:

  * Vertical crosshair
  * Tooltip includes:

    * Timestamp
    * Price
    * Ensemble score
    * Z-score
    * IF score
    * LSTM score

#### Grid:

* Very subtle gridlines (opacity < 10%)

---

## 5.2 ENSEMBLE SCORE PANEL

### Layout:

* Title
* Gauge
* Numeric score (center)
* Delta indicator
* Status label
* Context info

---

### Gauge Requirements:

* Arc thickness: **thin (max 8px)**
* Range: 0 → 1
* Marker at threshold (0.5)

---

### Numeric Score:

* Font size: 36px
* Must dominate visual hierarchy

---

### Delta Indicator:

* Format: `+0.12 ↑` or `-0.08 ↓`
* Color:

  * Increase → red
  * Decrease → green

---

### Status Label:

* Replace ANY wording implying action
* Must use:

  * “High Anomaly Detected”
  * “Moderate Activity”
  * “Normal Behavior”

---

### Context Info (mandatory):

* “Last anomaly: X min ago”
* “Model status: X/3 triggered”

---

## 5.3 MODEL DISTRIBUTION PANEL

### Structure:

* Title
* Agreement summary:

  > “2 of 3 models indicate anomaly”

---

### Bars:

Each model:

* Label
* Score
* Horizontal bar

---

### Rules:

* Above threshold → red
* Below threshold → muted blue

---

### Threshold lines:

* Must be visible on each bar

---

### Labels:

* “Above Threshold” ONLY
* No “Triggered”

---

## 5.4 ANOMALY HISTORY TABLE

### Columns:

* Timestamp
* Ticker
* Severity
* Trend
* Ensemble
* Status

---

### Severity Logic:

| Range   | Label  |
| ------- | ------ |
| <0.4    | LOW    |
| 0.4–0.5 | MEDIUM |
| >0.5    | HIGH   |

---

### Row Styling:

* High → red tint background
* Medium → amber tint
* Low → neutral

---

### Status:

* FLAGGED / NORMAL (text, not icon)

---

### Trend Column:

* Mini sparkline
* Color:

  * Rising → red
  * Falling → green

---

### Controls:

* Toggle: “Show flagged only”
* Dropdown: severity filter

---

## 6. INTERACTION RULES

### 6.1 Table Row Click

Opens modal:

Must show:

* Timestamp
* All model scores
* Ensemble score
* Explanation

---

### 6.2 Explanation (MANDATORY)

Format:

> “Detected due to volume spike + price divergence”

This must be present for every anomaly.

---

## 7. SENSITIVITY CONTROL

### Requirements:

* Show numeric value (e.g., 0.50)
* Show hint:

  > “Higher = more detections”

---

## 8. PERFORMANCE RULES

* No animation > 200ms
* No blocking UI updates
* Chart must not flicker on refresh

---

## 9. STRICT PROHIBITIONS

* No gradients beyond subtle cards
* No bright neon colors
* No unnecessary animations
* No unused whitespace
* No ambiguous labels
* No “AI-style” decorative UI

---

## 10. FINAL ACCEPTANCE CRITERIA

The UI is correct ONLY if:

* A user can identify anomaly risk in <5 seconds
* All components serve a decision purpose
* No element exists purely for aesthetics
* Information hierarchy is immediately clear

---

## FINAL NOTE

This system must feel like:

> an internal tool used by a trading desk

NOT:

> a student project or portfolio mockup
