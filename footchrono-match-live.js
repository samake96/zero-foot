(() => {
  const board = document.querySelector('[data-match-kickoff]');
  if (!board) return;
  const kickoff = Date.parse(board.dataset.matchKickoff);
  if (!Number.isFinite(kickoff)) return;
  let busy = false;
  let timer;
  const address = new URL(location.pathname, location.origin);
  address.searchParams.set('format', 'score');
  async function update() {
    if (Date.now() > kickoff + 5 * 3600000) {
      clearInterval(timer);
      return;
    }
    if (busy || document.hidden || Date.now() < kickoff - 45 * 60000) return;
    busy = true;
    try {
      const response = await fetch(address, {cache:'no-store', signal:AbortSignal.timeout(8000)});
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) return;
      const {score, status, finished} = await response.json();
      if (typeof score !== 'string' || typeof status !== 'string') return;
      const scoreNode = board.querySelector('.mc-score');
      const statusNode = board.querySelector('.mc-status');
      if (scoreNode.textContent !== score) scoreNode.textContent = score;
      if (statusNode.textContent !== status) statusNode.textContent = status;
      if (finished) clearInterval(timer);
    } catch {
      // Keep the last score when the connection is interrupted.
    } finally {
      busy = false;
    }
  }
  timer = setInterval(update, 30000);
  document.addEventListener('visibilitychange', update);
  update();
})();
