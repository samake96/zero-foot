export async function submitDraft(db, read, author, id) {
  const match = read('match');
  const title = read('title');
  const paragraphs = read('body').split(/\r?\n\s*\r?\n/).map(p => p.trim()).filter(Boolean);
  const urls = [...new Set(read('sources').split(/\s+/).filter(Boolean))];
  if (!/^[1-9][0-9]{0,14}$/.test(match) || !title || title.length > 160 ||
      !paragraphs.length || read('body').length > 12000 ||
      !urls.length || urls.length > 10 || read('sources').length > 3000) {
    return new Response('Renseignez le match, le titre, l’analyse et les sources.', {status:400});
  }
  const sources = [];
  for (const url of urls) {
    let parsed;
    try { parsed = new URL(url); } catch { return new Response('Lien de source invalide.', {status:400}); }
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password) {
      return new Response('Chaque source doit être une adresse HTTPS.', {status:400});
    }
    sources.push({url:parsed.href, label:parsed.hostname});
  }
  const content = JSON.stringify({title, paragraphs, sources});
  const result = await db.prepare(`INSERT INTO match_editorial_revisions (id, match_id, content, author)
    VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING`).bind(id, match, content, author).run();
  return new Response(null, {status:result.meta.changes ? 201 : 204});
}
