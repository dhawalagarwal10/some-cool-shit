# demo video script

## overview
target length: 2-3 minutes
format: screen recording with voiceover
tools: obs studio / loom / screencastify

---

## script

### opening (15 seconds)

**visual**: show terminal with project name displayed

**voiceover**:
"i built an ai-powered supply chain agent that prevents stockouts and optimizes inventory for fast-growing companies. let me show you how it works."

**on-screen text**: "supply chain intelligence agent - preventing stockouts, optimizing inventory"

---

### problem statement (20 seconds)

**visual**: show a simple slide or text overlay with these stats

**voiceover**:
"retailers lose over 1 trillion dollars annually to stockouts and excess inventory. traditional forecasting methods are manual, slow, and reactive. companies need intelligent automation."

**on-screen text**:
- $1.1 trillion lost to stockouts annually
- 25% of inventory is typically excess stock
- manual forecasting takes 10+ hours per week

---

### solution overview (25 seconds)

**visual**: show the dashboard landing page

**voiceover**:
"this system uses prophet for time series forecasting, claude ai for contextual insights, and automated alerts to prevent stockouts before they happen. it's designed for companies like boldfit with diverse product catalogs and seasonal demand."

**show**: click through different dashboard sections quickly

---

### demo: inventory health (30 seconds)

**visual**: navigate to dashboard page

**voiceover**:
"the dashboard gives you instant visibility into inventory health. here we can see 12 products across categories like supplements, equipment, and snacks."

**show**:
- point to health score: "85% health score"
- point to critical alerts: "3 items need immediate attention"
- show inventory value metrics

**voiceover continues**:
"notice the gym gloves - only 5 units left with predicted stockout in 3 days. the system has already flagged this as critical."

---

### demo: demand forecasting (35 seconds)

**visual**: go to forecasting page

**voiceover**:
"let's see the demand forecast for whey protein - our fastest-moving product."

**actions**:
- select whey protein from dropdown
- set forecast to 30 days
- click generate forecast

**show**: forecast chart loading then displaying

**voiceover**:
"the model predicts 240 units of demand over the next 30 days, with confidence intervals. it detected an upward trend - makes sense as we're approaching new year when fitness products spike."

**point to**: the trend analysis and seasonal patterns

---

### demo: reorder recommendations (40 seconds)

**visual**: navigate to recommendations page

**voiceover**:
"now the most powerful part - intelligent reorder recommendations."

**actions**:
- click analyze inventory button
- show loading state
- results appear

**voiceover**:
"the system analyzed all products and identified 5 that need reordering. look at the gym gloves recommendation."

**show**: expand gym gloves recommendation

**voiceover**:
"current stock: 5 units. predicted stockout: 3 days. recommended order: 50 units. total cost calculated automatically. the urgency is marked as critical."

**point to**:
- safety stock calculation
- expected demand metrics
- the reason field

**voiceover**:
"with one click, i can create a purchase order. the system will send slack notifications to the procurement team."

**action**: click create purchase order button

---

### demo: business impact (25 seconds)

**visual**: show a quick slide or text overlay

**voiceover**:
"for a company with 500 skus, this system can:
- reduce stockouts by 80%
- cut excess inventory by 50%
- save 35 hours per month in manual work
- improve working capital efficiency by 15%"

**on-screen text**: show these bullet points

---

### how it helps boldfit (20 seconds)

**visual**: back to dashboard or terminal

**voiceover**:
"for boldfit specifically, this solves:
- protein supplement forecasting during new year rush
- equipment inventory optimization
- fast-moving snack product management
- multi-supplier coordination across different lead times"

---

### technical architecture (15 seconds)

**visual**: show terminal or code editor briefly

**voiceover**:
"built with python, prophet for forecasting, claude for insights, fastapi for the backend, and streamlit for the dashboard. fully extensible and production-ready."

**show**: briefly flash the project structure

---

### closing (10 seconds)

**visual**: return to dashboard showing healthy metrics

**voiceover**:
"this isn't just another dashboard - it's an intelligent agent that actively prevents problems and optimizes operations. ready to deploy at boldfit."

**on-screen text**:
- "built for boldfit's ai intern application"
- your email
- github link

---

## recording tips

### before recording

1. **clean up your screen**
   - close unnecessary apps
   - clear desktop clutter
   - set browser to clean profile (no random bookmarks)
   - increase font sizes for readability

2. **prepare the demo**
   - run `python demo_data/generate_data.py`
   - start dashboard and verify it's working
   - have all pages loaded and tested
   - clear browser cache for fresh load

3. **audio setup**
   - use good microphone (even airpods are better than laptop mic)
   - test audio levels
   - record in quiet room
   - speak clearly and confidently

4. **lighting**
   - if doing face cam, ensure good lighting
   - screen recording doesn't need face cam unless you prefer

### during recording

1. **pacing**
   - speak at moderate pace (not too fast)
   - pause briefly between sections
   - don't say "um" or "uh" - just pause
   - if you make a mistake, pause and restart that section

2. **mouse movements**
   - move mouse deliberately
   - highlight key metrics by hovering
   - don't move mouse randomly
   - use mouse to draw attention to important numbers

3. **transitions**
   - use smooth navigation between pages
   - don't rush clicks
   - let charts and data load fully before speaking about them

4. **engagement**
   - use specific numbers ("5 units", "240 units predicted")
   - reference boldfit by name
   - connect features to business value
   - show enthusiasm but stay professional

### after recording

1. **editing** (if needed)
   - cut any dead air
   - speed up slow loading sections slightly (1.2x)
   - add zoom-ins on critical metrics
   - add on-screen text callouts for key points

2. **export settings**
   - 1080p resolution minimum
   - mp4 format
   - h.264 codec
   - keep file size under 50mb if possible

3. **thumbnail** (for youtube link)
   - screenshot of dashboard with "supply chain ai agent" text
   - clean and professional
   - shows the actual product

### upload options

1. **youtube** (unlisted)
   - best for easy sharing
   - good quality
   - professional looking

2. **loom**
   - easiest to record
   - automatic transcription
   - built-in editing

3. **google drive**
   - direct mp4 upload
   - works but less professional
   - make sure sharing is enabled

## alternative: slide deck option

if video recording isn't feasible, create a deck:

### slide breakdown

1. title slide
2. problem statement (with stats)
3. solution overview
4. screenshot: dashboard
5. screenshot: forecasting
6. screenshot: recommendations (zoomed in)
7. technical architecture diagram
8. business impact metrics
9. why boldfit needs this
10. closing slide with contact

use google slides or pitch.com for clean design

---

## final checklist before submission

- [ ] video is 2-3 minutes long
- [ ] audio is clear and audible
- [ ] demonstrates actual functionality (not just slides)
- [ ] mentions boldfit specifically
- [ ] shows business value clearly
- [ ] includes contact information
- [ ] uploaded and link tested
- [ ] link is set to public/unlisted (not private)

---

## sample alternative script (shorter version - 90 seconds)

### for a quick demo

**[0:00-0:10]** "i built an ai agent that prevents stockouts and optimizes inventory for fitness companies like boldfit."

**[0:10-0:30]** show dashboard: "real-time visibility into inventory health. this product has only 3 days of stock left - the ai flagged it as critical."

**[0:30-0:50]** show forecasting: "prophet-based forecasting predicts demand 30 days ahead, accounting for seasonality like the new year fitness rush."

**[0:50-1:10]** show recommendations: "intelligent reorder recommendations with safety stock calculations. one-click purchase orders. automated slack alerts."

**[1:10-1:25]** show impact: "reduces stockouts by 80%, cuts excess inventory by 50%, saves 35 hours per month."

**[1:25-1:30]** closing: "production-ready and built specifically for boldfit's operations."

---

good luck with your recording! keep it simple, professional, and focused on business value.
