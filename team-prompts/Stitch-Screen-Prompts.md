# Stitch Design Prompts — AirIntel (5 screens)
Paste the STYLE block first (or set it as your Stitch theme), then use each screen prompt.
Officer screens = dark "control-room" look. Citizen screen = light, friendly, mobile.
Tip: keep the real sample text in each prompt — real numbers make the design look finished, not empty.

================================================================
## 0. GLOBAL STYLE (use for every screen — keeps them consistent)
================================================================
Design a modern, premium data-dashboard web app called "AirIntel" — an AI air-quality command centre
for a smart city (Delhi). Style: clean, high-end SaaS control-room, think Linear + Stripe + a mission
dashboard. Professional and government-grade but sleek and futuristic.

Theme: dark mode. Background deep slate navy (#0F172A), cards slightly lighter (#1E293B) with soft
rounded corners (16px), thin subtle borders (#334155), and gentle shadows. Generous spacing, strong
visual hierarchy, lots of breathing room.

Typography: Inter (or similar clean geometric sans). Big bold numbers for key metrics, small
uppercase muted labels above them.

Air-quality colour scale (use consistently everywhere for AQI):
- Good = green #22C55E
- Moderate = yellow #EAB308
- Poor = orange #F97316
- Very Poor = red #EF4444
- Severe = dark maroon #7F1D1D
Use these as glowing status colours on cards, map areas, chips, and chart lines.

Accent colour: electric cyan/teal (#22D3EE) for buttons, highlights, and the AI/agent elements.
Add small clean line icons. Make it look award-winning and screenshot-ready.

================================================================
## 1. CITY DASHBOARD  (route "/")
================================================================
Design the main overview screen of the AirIntel air-quality dashboard (use the global dark style).

Top bar: left = "AirIntel" logo with a small air/wind icon; centre = city name "Delhi" with a live
green "LIVE" dot and timestamp "Updated 9:00 AM"; right = a search box and a user avatar.

Below, a row of 4 big KPI stat cards:
1. "City Average AQI" — huge number 196, an orange "POOR" pill, and a small up-arrow "+12 vs yesterday".
2. "Worst Ward" — "Rohini · 241" with a maroon "SEVERE" pill.
3. "Best Ward" — "Vasant Kunj · 88" with a green "MODERATE" pill.
4. "Wards in Severe Zone" — big number "6 of 24" with a small red progress ring.

Main area, two columns:
- Left (wider): a "City Trend — last 24h" line chart card, smooth area line coloured by AQI level,
  with a dotted "forecast +24h" continuation showing AQI rising to 230.
- Right: a "Mini Heat Map" card — a small stylised map of Delhi split into ward blocks, each block
  coloured by AQI (mix of green, yellow, orange, red, maroon), with a "View full map →" link.

Bottom: a horizontal "Top Alerts" strip — 3 small cards like "Rohini forecast to hit SEVERE in 18h",
each with an AQI colour bar and a small AI-spark icon.

Make it feel like a live mission control screen — glanceable, confident, impressive in 10 seconds.

================================================================
## 2. POLLUTION MAP  (route "/map")  — the hero screen
================================================================
Design a full-screen interactive city pollution map screen for AirIntel (global dark style). This is
the flagship screen, make it stunning.

Layout: a large interactive map fills about 70% of the screen (left/centre), showing Delhi divided
into ward polygons, each ward filled with a semi-transparent AQI colour (green → yellow → orange →
red → maroon) with soft glowing edges. Show ward labels faintly.

Floating on the top-left of the map: a segmented toggle control with 3 options —
"Current AQI" | "Predicted +24h" | "Dominant Source" — first one selected, in the cyan accent.

Bottom-left of the map: a compact colour legend for the AQI scale (Good → Severe).

Right side (30%): a "Ward Detail" side panel that appears when a ward is selected. Show:
- Ward name "Rohini" and a big AQI number "241" with a maroon "SEVERE" badge.
- Small pollutant chips: PM2.5 145, PM10 320, NO2 44.
- A mini "Why is it high?" section: a horizontal stacked bar split into Traffic 45%, Construction 25%,
  Industry 20%, Dust 10%, each in a distinct colour, with a confidence label "Confidence 78%".
- A tiny 24h forecast sparkline.
- A cyan button "Ask the AI about this ward".

Make the map look premium and alive, like Google Maps meets a data command centre.

================================================================
## 3. FORECAST SCREEN  (route "/forecast")
================================================================
Design an AQI forecast screen for AirIntel (global dark style).

Top: a title "AQI Forecast" with, on the right, a ward selector dropdown ("Rohini") and a segmented
time toggle "24h | 48h | 72h" (48h selected, cyan accent).

Main: one large forecast chart card taking most of the width — a smooth line/area chart of predicted
AQI over the next 48 hours. The line changes colour as it crosses AQI bands (yellow → orange → red →
maroon), with a soft shaded confidence band around it, and marker dots at +24h, +48h, +72h. Add a
subtle "danger threshold" dashed line at AQI 300.

Below the chart, a row of 3 summary cards:
- "+24h" → 214, orange "POOR", small "↑ rising".
- "+48h" → 268, red "VERY POOR", "↑ rising".
- "+72h" → 236, red "VERY POOR", "↓ falling".

Right or bottom: a small "AI Insight" card with a cyan spark icon and text like: "Pollution expected
to peak tomorrow evening due to low wind and rush-hour traffic. Consider early action."

Clean, data-focused, easy to read at a glance.

================================================================
## 4. GOVERNMENT DASHBOARD  (route "/government")
================================================================
Design a government action dashboard for AirIntel (global dark style) — for a city pollution officer.

Two-column layout.

Left column "Recommended Actions" (AI-generated): a vertical list of action cards, each with:
- A coloured urgency tag (HIGH = red, MEDIUM = orange, LOW = yellow).
- A bold action title, e.g. "Restrict diesel trucks on Ring Road, 6–10 AM".
- A target line "Ring Road corridor".
- A one-line reason "Traffic is 45% of load; severe forecast tomorrow AM".
Show 3–4 such cards. Add a small "Generated by AI" cyan chip at the top of this column.

Below actions: an "Inspection Priority" mini table with columns Site | Ward | Reason | Priority,
priority shown as a coloured number badge (1 = red). 3 rows of sample data.

Right column "Officer Assistant" — a chat panel:
- A chat header "Ask AirIntel".
- A conversation: officer bubble "Which ward should inspectors visit first?" and an AI bubble
  answering "Rohini — AQI 241 (severe), mostly traffic. It stays severe through tomorrow morning."
- Under the AI reply, small grey chips: "used: AQI, Source, Forecast".
- A message input box at the bottom with a cyan send button and 3 suggested-question chips above it.

Make it feel like a serious decision-making tool that a real commissioner would trust.

================================================================
## 5. CITIZEN VIEW  (route "/citizen")  — LIGHT + MOBILE
================================================================
Design a friendly mobile-first citizen health screen for AirIntel. Different mood from the dashboards:
LIGHT theme, warm, calm, and very simple — one screen, no clutter. Soft white/very-light background,
rounded cards, big friendly text, the same AQI colour scale for status.

Top: a location row "📍 Rohini, Delhi" with a language dropdown on the right (English / हिंदी /
ਪੰਜਾਬੀ).

Hero card: a large circular AQI gauge showing "241" in the centre, ring coloured maroon, with the
word "SEVERE" and a short line "Air is unhealthy today".

Below, a "Your Advice" card (personalised): friendly plain-language guidance, e.g. "Avoid outdoor
jogging before noon. Wear an N95 mask outside. Keep windows closed in the evening." Add a small
selector row of context chips: Asthma · Jogger · Elderly · Child (Asthma selected).

Two side-by-side small cards:
- "Best time outdoors" → green, "3–5 PM".
- "Worst time outdoors" → red, "7–10 AM".

A simple 24-hour mini forecast strip of coloured dots so a citizen can see when air gets better.

Bottom: one clear button "Get today's advice" in a calm green/teal.

Keep it warm, reassuring, and effortless — something a normal person understands in 5 seconds.
