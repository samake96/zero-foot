// Cloudflare Access JWT verification; never trust client-supplied email/user headers.
export async function accessIdentity(request,env){
 const domain=String(env.ACCESS_TEAM_DOMAIN||'').replace(/^https?:\/\//,'').replace(/\/$/,'');
 const audience=String(env.ACCESS_AUD||'');
 if(!/^[a-z0-9-]+\.cloudflareaccess\.com$/.test(domain)||!audience) return null;
 const header=request.headers.get('cf-access-jwt-assertion');
 const cookie=(request.headers.get('cookie')||'').match(/(?:^|;\s*)CF_Authorization=([^;]+)/)?.[1];
 const token=header||cookie;
 if(!token)return null;
 const parts=token.split('.');if(parts.length!==3)return null;
 const decode=s=>JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(s.length/4)*4,'=')),c=>c.charCodeAt(0))));
 let head,payload;try{head=decode(parts[0]);payload=decode(parts[1])}catch{return null}
 const now=Math.floor(Date.now()/1000);
 if(head.alg!=='RS256'||typeof head.kid!=='string'||payload.iss!=='https://'+domain||
 !Array.isArray(payload.aud)||!payload.aud.includes(audience)||typeof payload.sub!=='string'||
 !Number.isFinite(payload.exp)||payload.exp<=now||!Number.isFinite(payload.iat)||payload.iat>now+60)return null;
 try{
  const response=await fetch('https://'+domain+'/cdn-cgi/access/certs',{cf:{cacheTtl:300,cacheEverything:true}});
  if(!response.ok)return null;
  const jwks=await response.json();const key=jwks.keys?.find(k=>k.kid===head.kid&&k.kty==='RSA');
  if(!key)return null;
  const publicKey=await crypto.subtle.importKey('jwk',key,{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['verify']);
  const signature=Uint8Array.from(atob(parts[2].replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(parts[2].length/4)*4,'=')),c=>c.charCodeAt(0));
  const bytes=new TextEncoder().encode(parts[0]+'.'+parts[1]);
  if(!await crypto.subtle.verify('RSASSA-PKCS1-v1_5',publicKey,signature,bytes))return null;
  return {id:payload.sub,name:typeof payload.email==='string'?payload.email.split('@')[0].slice(0,40):'Supporter'};
 }catch{return null}
}
