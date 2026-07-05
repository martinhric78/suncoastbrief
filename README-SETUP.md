# The Suncoast Brief — Automatic Newsroom

## What the robot does, every day, by itself
- **8:45 PM:** builds tomorrow's issue — real NWS weather for coast & inland,
  NOAA tide times, sunrise/sunset, alert bar, fresh local headlines — and opens
  a Pull Request titled "🌅 Tomorrow's Brief — tap Merge to approve."
- **You (9 PM):** open the GitHub app notification → read → **tap Merge.** That IS the approval.
- **Within ~2 min of Merge:** the live site updates itself (GitHub Pages).
- **4:30 AM:** robot re-pulls the freshest weather and publishes it directly — no approval needed.
- **All day:** the site itself rotates Catch of the Day, Grow & Eat, Free Day Out,
  Bible verse, wisdom words, horoscopes, and the date — automatically.

## One-time setup (10 minutes)
1. Create repo **suncoastbrief** (Public) → upload ALL these files (keep the `.github` folder!).
2. Settings → Pages → Source: branch **main**, folder **/ (root)** → Save.
3. Settings → Actions → General → Workflow permissions → **Read and write** → Save.
4. Actions tab → run **"Nightly draft"** once manually (Run workflow) → confirm a PR appears → Merge it. That's your test flight.
5. Install the **GitHub mobile app** and allow notifications — that's your nightly "approve" button.

## What stays human (on purpose)
- Deeper local stories, events, and the daily real adoptable pet photo: edit any evening
  with Claude in the project chat, or directly in the PR. The robot never overwrites these.
- The Beehiiv email: paste + schedule for 5 AM (~5 min) until email automation is added.

## If something breaks
The robot fails safe: any source that's down means that section simply keeps
yesterday's content — the page never breaks. Check the Actions tab for logs.
