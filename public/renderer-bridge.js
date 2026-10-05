window.voiceControls={gain:1,offsets:[0,0,0,0,0,0]};
let audioContext,source,activeId,generation=0,clockTimer;
window.voiceSpeaking=false;window.voicePause=false;window.voiceIdleMode='gentle';window.voiceIdleSpeed=.45;
function portraitActivity(speaking){
 window.voiceSpeaking=speaking;
 if(typeof videoProcessor==='undefined'||!videoProcessor.video)return;
 const still=!speaking&&window.voiceIdleMode==='still';
 videoProcessor.video.playbackRate=speaking||window.voiceIdleMode==='source'?1:window.voiceIdleSpeed;
 if(!still)videoProcessor.play();else{videoProcessor.pause();if(window.voiceIdleCanvas){ctx_video.clearRect(0,0,canvas_video.width,canvas_video.height);ctx_video.drawImage(window.voiceIdleCanvas,0,0)}}
}
const tell=(type,details={})=>parent.postMessage({type,...details},location.origin);
window.addEventListener('error',e=>tell('renderer-error',{message:e.message,id:activeId}));
window.addEventListener('unhandledrejection',e=>tell('renderer-error',{message:String(e.reason),id:activeId}));
const poll=setInterval(()=>{if(typeof Module!=='undefined'&&Module._setAudioBuffer&&typeof dataSets!=='undefined'&&dataSets.length&&window.voiceIdleCanvas){clearInterval(poll);window.rendererReady=true;silence();tell('ready')}},250);
function silence(){
 generation++;clearInterval(clockTimer);window.voicePause=false;portraitActivity(false);
 if(source){source.onended=null;try{source.stop()}catch{}source=null}
 if(typeof Module!=='undefined'&&Module._setAudioBuffer){
  const b=new ArrayBuffer(364),d=new DataView(b),s=(o,t)=>[...t].forEach((c,i)=>d.setUint8(o+i,c.charCodeAt(0)));
  s(0,'RIFF');d.setUint32(4,356,true);s(8,'WAVE');s(12,'fmt ');d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,1,true);d.setUint32(24,16000,true);d.setUint32(28,32000,true);d.setUint16(32,2,true);d.setUint16(34,16,true);s(36,'data');d.setUint32(40,320,true);
  const p=Module._malloc(b.byteLength);Module.HEAPU8.set(new Uint8Array(b),p);Module._setAudioBuffer(p,b.byteLength);Module._free(p);
 }
}
window.addEventListener('message',async e=>{
 if(e.origin!==location.origin||e.source!==parent)return;
 const m=e.data;
 try{
  if(m.type==='controls'){window.voiceControls=m.controls;if(!window.voiceSpeaking&&window.voiceIdleMode==='still')window.voiceIdleCanvas=null;return}
  if(m.type==='idle'){window.voiceIdleMode=['gentle','source','still'].includes(m.mode)?m.mode:'gentle';window.voiceIdleSpeed=Math.max(.2,Math.min(.8,Number(m.speed)||.45));portraitActivity(window.voiceSpeaking);return}
  if(m.type==='stop'){silence();return}
  if(m.type==='avatar'){silence();const select=document.querySelector('#characterDropdown');select.value=m.asset;select.dispatchEvent(new Event('change'));return}
  if(m.type==='unlock'){audioContext??=new AudioContext();await audioContext.resume();return}
  if(m.type!=='speak')return;
  silence();const version=generation;activeId=m.id;
  audioContext??=new AudioContext();await audioContext.resume();if(version!==generation)return;
  const bytes=Uint8Array.from(atob(m.audio),c=>c.charCodeAt(0));
  const decoded=await audioContext.decodeAudioData(bytes.buffer.slice(0));if(version!==generation)return;
  const p=Module._malloc(bytes.length);Module.HEAPU8.set(bytes,p);Module._setAudioBuffer(p,bytes.length);Module._free(p);
  source=audioContext.createBufferSource();source.buffer=decoded;source.connect(audioContext.destination);
  const segments=Array.isArray(m.segments)?m.segments:[];let segmentIndex=-2;
  source.onended=()=>{silence();tell('speech-ended',{id:m.id})};portraitActivity(true);
  const started=audioContext.currentTime;source.start();tell('speech-started',{id:m.id,duration:decoded.duration});
  const tick=()=>{
   if(version!==generation)return;
   const elapsed=Math.min(decoded.duration,Math.max(0,audioContext.currentTime-started));
   const index=segments.findIndex(s=>elapsed>=s.start&&elapsed<s.start+s.duration);
   if(index!==segmentIndex){segmentIndex=index;window.voicePause=segments[index]?.kind==='pause';portraitActivity(!window.voicePause);tell('segment-started',{id:m.id,index,elapsed,segment:segments[index]||null})}
   tell('speech-progress',{id:m.id,elapsed,duration:decoded.duration,index});
  };tick();clockTimer=setInterval(tick,50);
 }catch(err){silence();tell('renderer-error',{message:String(err),id:m.id})}
});
