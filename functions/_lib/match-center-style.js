export const matchCenterStyle = `
.mc-center { --mc-accent: #8beac0; }
.mc-nav { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; }
.mc-nav a {
  display: inline-flex; align-items: center; min-height: 44px;
  padding: .35rem .8rem; border: 1px solid var(--line); border-radius: .6rem;
  color: var(--text); text-decoration: none;
}
.mc-nav a:hover, .mc-nav a:focus-visible { border-color: var(--mc-accent); }
.mc-section {
  margin-bottom: 1rem; padding: clamp(.8rem, 3vw, 1.6rem); border: 1px solid var(--line);
  border-radius: .9rem; background: var(--panel); scroll-margin-top: 1rem;
}
.mc-section :is(h2, h3) { margin-top: 0; }
.mc-kicker, .mc-note { color: var(--muted); font-size: .92rem; }
.mc-kicker { margin-top: 0; }
.mc-scoreboard {
  display: grid; grid-template-columns: minmax(0,1fr) minmax(5rem,auto) minmax(0,1fr);
  align-items: center; gap: .5rem; text-align: center;
}
.mc-scoreboard > div { display: grid; justify-items: center; gap: .4rem; overflow-wrap: anywhere; }
.mc-score { font-size: clamp(1.55rem, 5vw, 2.75rem); font-variant-numeric: tabular-nums; white-space: nowrap; }
.mc-status { color: var(--mc-accent); font-size: .8rem; }
.mc-form { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 1.2rem; }
.mc-results { list-style: none; padding: 0; margin: 0; }
.mc-result {
  display: grid; grid-template-columns: minmax(0,1fr) auto; gap: .25rem .65rem;
  padding: .65rem 0; border-top: 1px solid var(--line);
}
.mc-result-info { grid-column: 1/-1; display: flex; gap: .55rem; flex-wrap: wrap; font-size: .78rem; color: var(--muted); }
.mc-result-teams > div { display: flex; justify-content: space-between; gap: .5rem; }
.mc-result-teams span { overflow-wrap: anywhere; }
.mc-outcome { align-self: center; min-width: 1.7rem; padding: .2rem; text-align: center; border-radius: .35rem; font-weight: 750; }
.mc-outcome.win { background: #173c32; color: #a0f3c5; }
.mc-outcome.draw { background: #413723; color: #ffe4a0; }
.mc-outcome.loss { background: #492831; color: #ffc1c7; }
.mc-source { font-size: .78rem; grid-column: 1/-1; }
@media(max-width:640px) { .mc-form { grid-template-columns: 1fr; } }

.fc-brand img { display: block; width: clamp(150px, 23vw, 205px); height: auto; }
main:has(.mc-center) > h1 { font-size: clamp(1.28rem, 4.5vw, 2rem); margin-block: .65rem; }
.mc-center .mc-nav { margin: .65rem 0 1rem; }
.mc-scoreboard img {
  box-sizing: content-box; padding: 8px; border-radius: 12px;
  background: #eef4fb; object-fit: contain;
}
@media(max-width:640px) {
  body:has(.mc-center) .fc-nav {
    flex-wrap: nowrap; overflow-x: auto; min-width: 0;
  }
  body:has(.mc-center) .fc-nav a { flex: none; }
  .mc-scoreboard img { width: 38px; height: 38px; }
}
`;
