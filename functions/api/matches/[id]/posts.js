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
