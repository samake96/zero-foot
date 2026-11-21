
import {accessIdentity} from '../../../_lib/auth.js';
export async function onRequestPost({request,env,params}){
 const id=params.id;if(!validMatch(id))return json({error:'Invalid match'},400);
 if(!env.COMMUNITY_DB)return json({error:'Community unavailable'},503);
 const user=await accessIdentity(request,env);
 if(!user)return json({error:'Authentication required'},401);
 if(!/^application\/json(?:;|$)/i.test(request.headers.get('content-type')||''))return json({error:'JSON required'},415);
 const len=Number(request.headers.get('content-length')||0);
 if(len>5000)return json({error:'Payload too large'},413);
 let input;try{const raw=await request.text();if(raw.length>5000)return json({error:'Payload too large'},413);input=JSON.parse(raw)}catch{return json({error:'Invalid JSON'},400)}
 const body=typeof input?.body==='string'?input.body.trim():'';
 if(body.length<2||body.length>1000)return json({error:'Message must contain 2–1000 characters'},400);
 const parent=typeof input?.parent_id==='string'?input.parent_id:null;
 if(parent&&!/^[0-9a-f-]{36}$/i.test(parent))return json({error:'Invalid reply'},400);
 try{
  if(parent){const p=await env.COMMUNITY_DB.prepare("SELECT id,parent_id FROM community_posts WHERE id=? AND match_id=? AND status='visible'").bind(parent,id).first();if(!p||p.parent_id)return json({error:'Reply target unavailable'},400)}
  const recent=await env.COMMUNITY_DB.prepare("SELECT COUNT(*) AS count FROM community_posts WHERE user_id=? AND created_at>strftime('%Y-%m-%dT%H:%M:%fZ','now','-1 minute')").bind(user.id).first();
  if((recent?.count||0)>=3)return json({error:'Too many messages, try again later'},429);
  const uuid=crypto.randomUUID();
  await env.COMMUNITY_DB.prepare("INSERT INTO community_posts(id,match_id,user_id,display_name,parent_id,body) VALUES(?,?,?,?,?,?)").bind(uuid,id,user.id,user.name,parent,body).run();
  return json({id:uuid,created:true},201);
 }catch{return json({error:'Unable to publish message'},503)}
}
const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}});
const validMatch=id=>/^[a-zA-Z0-9_-]{1,80}$/.test(id||'');
export async function onRequestGet({request,env,params}){
 const id=params.id;if(!validMatch(id))return json({error:'Invalid match'},400);
 if(!env.COMMUNITY_DB)return json({available:false,posts:[],reason:'Community database not configured'},503);
 const url=new URL(request.url),cursor=url.searchParams.get('cursor');
 if(cursor&&(!/^\d{4}-\d\d-\d\dT/.test(cursor)||cursor.length>40))return json({error:'Invalid cursor'},400);
 const limit=30;
 const statement=cursor?
 env.COMMUNITY_DB.prepare("SELECT id,match_id,display_name,parent_id,body,created_at FROM community_posts WHERE match_id=? AND status='visible' AND created_at<? ORDER BY created_at DESC LIMIT ?").bind(id,cursor,limit):
 env.COMMUNITY_DB.prepare("SELECT id,match_id,display_name,parent_id,body,created_at FROM community_posts WHERE match_id=? AND status='visible' ORDER BY created_at DESC LIMIT ?").bind(id,limit);
 try{const {results}=await statement.all();return json({available:true,posts:results,next_cursor:results.length===limit?results.at(-1).created_at:null})}catch{return json({error:'Community temporarily unavailable'},503)}
}
