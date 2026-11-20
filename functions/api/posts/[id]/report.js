import {accessIdentity} from '../../_lib/auth.js';
const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}});
export async function onRequestPost({request,env,params}){
 if(!env.COMMUNITY_DB)return json({error:'Community unavailable'},503);
 const user=await accessIdentity(request,env);if(!user)return json({error:'Authentication required'},401);
 const postId=params.id;if(!/^[0-9a-f-]{36}$/i.test(postId||''))return json({error:'Invalid post'},400);
 let input;try{const raw=await request.text();if(raw.length>2000)throw Error();input=JSON.parse(raw)}catch{return json({error:'Invalid JSON'},400)}
 const reason=typeof input.reason==='string'?input.reason.trim():'';
 if(reason.length<5||reason.length>300)return json({error:'Reason must contain 5–300 characters'},400);
 try{
  const post=await env.COMMUNITY_DB.prepare("SELECT id FROM community_posts WHERE id=? AND status='visible'").bind(postId).first();
  if(!post)return json({error:'Post unavailable'},404);
  await env.COMMUNITY_DB.prepare("INSERT OR IGNORE INTO community_reports(id,post_id,reporter_id,reason) VALUES(?,?,?,?)").bind(crypto.randomUUID(),postId,user.id,reason).run();
  return json({reported:true},201);
 }catch{return json({error:'Report unavailable'},503)}
}
