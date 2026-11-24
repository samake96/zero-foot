import {submitDraft} from '../_lib/editorial-draft.js';
import {accessIdentity} from '../_lib/auth.js';
import {escape} from '../_lib/public-football.js';

const route = '/redaction/';
const headers = {
  'Content-Type': 'text/html; charset=utf-8',
  'Cache-Control': 'private, no-store',
  'X-Robots-Tag': 'noindex, nofollow',
  'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'",
};
const response = (body, status = 200) => new Response(body, {headers, status});

async function permissions(request, env) {
  const user = await accessIdentity(request, {...env, ACCESS_AUD:env.EDITORIAL_ACCESS_AUD || env.ACCESS_AUD});
  if (!user?.email) return null;
  const includes = value => String(value || '').split(',').some(email => email.trim().toLowerCase() === user.email);
  const write = includes(env.EDITORIAL_WRITERS);
  const review = includes(env.EDITORIAL_REVIEWERS);
  const soleEditor = write && review &&
    String(env.EDITORIAL_WRITERS).trim().toLowerCase() === user.email &&
    String(env.EDITORIAL_REVIEWERS).trim().toLowerCase() === user.email;
  return write || review ? {write, review, soleEditor, id:user.id} : null;
}

const writeForm = `<form method="post" action="${route}">
  <input type="hidden" name="action" value="submit">
  <label>Identifiant du match <input name="match" required inputmode="numeric" pattern="[1-9][0-9]{0,14}"></label>
  <label>Titre <input name="title" required maxlength="160"></label>
  <label>Analyse <textarea name="body" required maxlength="12000" rows="9" placeholder="Séparez les paragraphes par une ligne vide."></textarea></label>
  <label>Sources vérifiées <textarea name="sources" required maxlength="3000" rows="3" placeholder="Une adresse HTTPS par ligne"></textarea></label>
  <button>Soumettre à la relecture</button>
</form>`;

export async function onRequestGet({request, env}) {
  const role = await permissions(request, env);
  if (!role) return response('Accès réservé à la rédaction.', 403);
  try {
    const {results} = await env.COMMUNITY_DB.prepare(`SELECT id, match_id, content, author
      FROM match_editorial_revisions WHERE state = 'pending' ORDER BY created_at, id LIMIT 50`).all();
    const items = results.map(row => {
      const content = JSON.parse(row.content);
      const controls = role.review && (role.soleEditor || role.id !== row.author) ? `<form method="post" action="${route}">
        <input type="hidden" name="revision" value="${escape(row.id)}">
        <label>Note de relecture <input name="note" required maxlength="1000"></label>
        <button name="action" value="publish">Publier</button>
        <button name="action" value="reject">Refuser</button>
      </form>` : '';
      return `<article><h3>${escape(content.title)}</h3>
        <p><a href="/matchs/${escape(row.match_id)}">Ouvrir la fiche du match</a></p>
        ${content.paragraphs.map(p => `<p>${escape(p)}</p>`).join('')}
        <ul>${content.sources.map(s => `<li><a href="${escape(s.url)}" rel="noreferrer">${escape(s.url)}</a></li>`).join('')}</ul>
        ${controls}</article>`;
    }).join('');
    return response(`<!doctype html><html lang="fr"><meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Rédaction FootChrono</title><style>
      body{max-width:48rem;margin:2rem auto;padding:0 1rem;font:1rem/1.6 system-ui;color:#172437}
      form,article{border:1px solid #bfced9;border-radius:.6rem;padding:1rem;margin-bottom:1rem}
      label{display:block;margin-bottom:1rem} input:not([type=hidden]),textarea{display:block;width:100%;box-sizing:border-box;font:inherit}
      button{font:inherit;padding:.5em .8em} article{overflow-wrap:anywhere}</style>
      <h1>Rédaction FootChrono</h1>${role.write ? writeForm : ''}
      <h2>Analyses à relire</h2>${items || '<p>Aucune analyse en attente.</p>'}</html>`);
  } catch {
    return response('Espace rédaction temporairement indisponible.', 503);
  }
}

export async function onRequestPost({request, env}) {
  const role = await permissions(request, env);
  if (!role || request.headers.get('Origin') !== new URL(request.url).origin) {
    return response('Accès refusé.', 403);
  }
  if (Number(request.headers.get('Content-Length')) > 100000 ||
      !request.headers.get('Content-Type')?.startsWith('application/x-www-form-urlencoded')) {
    return response('Formulaire invalide.', 400);
  }
  const body = await request.text();
  if (body.length > 100000) return response('Formulaire trop long.', 413);
  const fields = new URLSearchParams(body);
  const read = key => (fields.get(key) || '').trim();
  const action = read('action');
  const db = env.COMMUNITY_DB;
  try {
    if (action === 'submit' && role.write) {
      const draft = await submitDraft(db, read, role.id, crypto.randomUUID());
      if (!draft.ok) return response(await draft.text(), draft.status);
    } else if (['publish', 'reject'].includes(action) && role.review) {
      const revision = read('revision');
      const note = read('note');
      if (!revision || !note || note.length > 1000) return response('Ajoutez une note de relecture.', 400);
      const decision = db.prepare(`UPDATE match_editorial_revisions SET state = ?, reviewer = ?,
        decision_note = ?, reviewed_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
        WHERE id = ? AND state = 'pending' AND (author <> ? OR ? = 1)`)
        .bind(action === 'publish' ? 'published' : 'rejected', role.id, note, revision, role.id, Number(role.soleEditor));
      const results = action === 'publish' ? await db.batch([
        db.prepare(`UPDATE match_editorial_revisions SET state = 'superseded'
          WHERE state = 'published' AND match_id = (SELECT match_id FROM match_editorial_revisions
            WHERE id = ? AND state = 'pending' AND (author <> ? OR ? = 1))`).bind(revision, role.id, Number(role.soleEditor)),
        decision,
      ]) : [await decision.run()];
      if (!results.at(-1).meta.changes) return response('Cette révision ne peut plus être traitée par ce compte.', 409);
    } else {
      return response('Action non autorisée.', 403);
    }
    return new Response(null, {status:303, headers:{...headers, Location:route}});
  } catch {
    return response('Impossible d’enregistrer cette action pour le moment.', 503);
  }
}
