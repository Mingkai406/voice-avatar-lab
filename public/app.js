const $=id=>document.getElementById(id),events=[];
let sampleMode=false;
let history=[],stage=0,patientState={},last='',lastPlan=[],busy=false,ready=false,epoch=0,recorder,chunks=[],stream,recordTimer,segments=[];
const log=(type,data={})=>events.push({time:new Date().toISOString(),type,...data});
const send=m=>$('avatar').contentWindow.postMessage(m,location.origin);
const notice=s=>$('notice').textContent=s;
async function api(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const d=await r.json();if(!r.ok)throw Error(d.error||r.statusText);return d}
function message(role,text){$('messages').querySelector('.empty')?.remove();const el=document.createElement('div');el.className='message '+role;const label=document.createElement('strong');label.textContent=role==='user'?'You':'Alex';const p=document.createElement('p');p.textContent=text;el.append(label,p);$('messages').append(el);$('messages').scrollTop=$('messages').scrollHeight}
function setBusy(v){busy=v;$('send').disabled=v;$('replay').disabled=v||!last;$('mic').disabled=v||sampleMode;$('testVoice').disabled=v;$('replayPlan').disabled=v||!last;document.querySelectorAll('[data-prompt]').forEach(b=>b.disabled=v)}
function settings(){return {rate:+$('rate').value,pause:+$('pause').value,voice:$('voice').value,rhythm:$('rhythm').value,hesitation:+$('hesitation').value,backend:$('backend').value,neural_voice:$('neuralVoice').value,delivery:$('delivery').value}}
function clearPlayback(label='Ready'){$('playbackTime').textContent=label;$('playbackFill').style.width='0%';$('timeline').querySelectorAll('.active').forEach(e=>e.classList.remove('active'));$('segmentDetail').textContent='Follow the actual audio as it plays.'}
function cancel(label='Stopped'){epoch++;send({type:'stop'});clearPlayback(label);setBusy(false);$('phase').textContent=label;return epoch}
function showTimeline(d){segments=d.segments||[];$('timeline').replaceChildren();if(!segments.length){const el=document.createElement('span');el.className='help';el.textContent='Continuous speech';$('timeline').append(el)}for(const [index,s] of segments.entries()){const el=document.createElement('span');el.className='segment '+s.kind;el.dataset.index=index;el.textContent=s.kind==='pause'?s.duration.toFixed(2)+'s':s.text;el.title=`${s.label||s.kind} · ${s.start.toFixed(2)}s–${(s.start+s.duration).toFixed(2)}s`;$('timeline').append(el)}$('playbackTime').textContent='Prepared · '+d.duration.toFixed(1)+'s'}
function renderPauseEditor(){
 const pauses=lastPlan.map((event,index)=>({event,index})).filter(x=>x.event.kind==='pause');
 $('pauseEditor').hidden=!last||$('rhythm').value!=='planned'||!pauses.length;$('pauseRows').replaceChildren();
 for(const {event,index} of pauses){
  const row=document.createElement('label');row.className='pause-row';const title=document.createElement('span');
  title.textContent=`After “${lastPlan[index-1]?.text||'…'}” · ${event.label}`;
  const input=document.createElement('input');input.type='number';input.min=0;input.max=5;input.step=.05;
  input.value=((event.duration_ms??Math.min(5000,+$('hesitation').value*(event.scale??1)))/1000).toFixed(2);
  input.setAttribute('aria-label',`Pause after ${lastPlan[index-1]?.text||'fragment'} in seconds`);
  input.onchange=()=>{const value=input.valueAsNumber;if(!Number.isFinite(value)){renderPauseEditor();return}event.duration_ms=Math.round(Math.max(0,Math.min(5,value))*1000);input.value=(event.duration_ms/1000).toFixed(2);$('pauseEditStatus').textContent='Timing changed. Replay to hear it; the current audio is unchanged.';log('pause-edit',{index,duration_ms:event.duration_ms})};
  const unit=document.createElement('span');unit.textContent='s';row.append(title,input,unit);$('pauseRows').append(row);
 }
}
$('replayPlan').onclick=()=>$('replay').click();
$('resetPauses').onclick=()=>{for(const event of lastPlan)delete event.duration_ms;renderPauseEditor();$('pauseEditStatus').textContent='Suggested timing restored. Replay to hear it.'};
async function speak(text,token,plan=[]){
 const s=settings();$('phase').textContent='Preparing audio';notice(sampleMode?'Preparing recorded examples with your pause settings.':s.backend==='qwen3'?'Generating neural speech on this Mac. The first reply may take longer.':'Preparing speech on this Mac…');
 const d=await api('/api/say',{text,...s,plan});if(token!==epoch)return;
 showTimeline(d);renderPauseEditor();if(text!==last)$('pauseEditor').hidden=true;log('audio-ready',{duration:d.duration,segments:d.segments,preparation_s:d.preparation_s,...s});send({type:'speak',audio:d.audio,id:token,segments:d.segments});
 $('metrics').textContent=`${s.backend==='qwen3'?'Qwen3-TTS':'System voice'} · prepared in ${d.preparation_s.toFixed(1)}s · audio ${d.duration.toFixed(1)}s`;
 notice(d.quality_retry||d.quality_retries?.length?'An unusually long speech segment was regenerated with Calm delivery.':s.backend==='qwen3'?'Neural speech generated locally. Timing follows the prepared audio.':'Speech ready. Planned pauses are included in the audio.');
}
async function submit(text){
 if(busy||!text.trim())return;if(!ready){notice('Portrait is still loading. Please wait.');return}
 const token=cancel('Preparing response');send({type:'unlock'});setBusy(true);message('user',text);$('prompt').value='';notice('Preparing a response…');
 try{const mode=$('mode').value;const d=await api('/api/chat',{prompt:text,mode,profile:$('profile').value,history,stage,patient_state:patientState});if(token!==epoch)return;
  history.push({role:'user',content:text},{role:'assistant',content:d.text});stage=d.stage;patientState=d.patient_state||{};last=d.text;lastPlan=d.plan||[];renderPauseEditor();$('pauseEditStatus').textContent='Changes apply on replay.';message('assistant',last);
  if(mode==='cue'){$('retrievalState').textContent=stage===3?'Word retrieved':stage===1?'Meaning available':'Word not yet retrieved';$('cueReason').textContent=d.reason}
  log('turn',{input:text,output:last,mode,stage,patient_state:patientState,reason:d.reason,generation_s:d.generation_s,plan:lastPlan});await speak(last,token,lastPlan);
 }catch(e){if(token===epoch){notice(e.message);$('phase').textContent='Ready to retry';clearPlayback('Not playing')}}finally{if(token===epoch)setBusy(false)}
}
$('chatForm').onsubmit=e=>{e.preventDefault();submit($('prompt').value)};
document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>submit(b.dataset.prompt));
window.addEventListener('message',e=>{
 if(e.origin!==location.origin||e.source!==$('avatar').contentWindow)return;const m=e.data;
 if(m.type==='ready'){ready=true;$('avatarStatus').textContent='Ready';$('phase').textContent='Ready to listen';controls();idleControls();return}
 if(m.type==='renderer-error'){if(m.id!=null&&m.id!==epoch)return;notice('Portrait: '+m.message);log('error',{message:m.message});clearPlayback('Playback error');$('phase').textContent='Ready to retry';return}
 if(m.id!==epoch)return;
 if(m.type==='speech-started'){$('phase').textContent='Speaking';log(m.type,{id:m.id})}
 if(m.type==='speech-ended'){$('phase').textContent='Ready to listen';$('playbackTime').textContent='Finished';$('playbackFill').style.width='100%';$('timeline').querySelectorAll('.active').forEach(x=>x.classList.remove('active'));$('segmentDetail').textContent='Finished. Replay with different settings to compare.';log(m.type,{id:m.id})}
 if(m.type==='segment-started'){
  $('timeline').querySelectorAll('.active').forEach(x=>x.classList.remove('active'));const el=$('timeline').querySelector(`[data-index="${m.index}"]`);el?.classList.add('active');
  const s=m.segment;if(s){$('phase').textContent=s.kind==='pause'?s.label:'Speaking';$('segmentDetail').textContent=s.kind==='pause'?`${s.label} · ${s.duration.toFixed(2)}s · planned silence`:`Alex: ${s.text}`;log('segment-executed',{id:m.id,index:m.index,planned_start:s.start,playback_time:m.elapsed,kind:s.kind})}
 }
 if(m.type==='speech-progress'){$('playbackTime').textContent=`${m.elapsed.toFixed(1)} / ${m.duration.toFixed(1)}s`;$('playbackFill').style.width=(100*m.elapsed/m.duration)+'%'}
});
$('stop').onclick=()=>{cancel();if(recorder?.state==='recording'){recorder.onstop=null;recorder.stop();stream?.getTracks().forEach(t=>t.stop());clearTimeout(recordTimer);$('mic').textContent='Record'}log('stop')};
$('replay').onclick=async()=>{if(!last||busy)return;const token=cancel('Preparing audio');send({type:'unlock'});setBusy(true);try{await speak(last,token,lastPlan)}catch(e){if(token===epoch){notice(e.message);$('phase').textContent='Ready to retry'}}finally{if(token===epoch)setBusy(false)}};
function reset(){cancel('Ready to listen');if(recorder?.state==='recording'){recorder.onstop=null;recorder.stop();stream?.getTracks().forEach(t=>t.stop());clearTimeout(recordTimer);$('mic').textContent='Record'}history=[];stage=0;patientState={};last='';lastPlan=[];segments=[];renderPauseEditor();$('metrics').textContent='';$('messages').replaceChildren();$('timeline').replaceChildren();$('retrievalState').textContent='Word not yet retrieved';$('cueReason').textContent='Compare encouragement, a meaning cue and a sound cue.';setBusy(false);log('reset');notice('New conversation.')}
$('reset').onclick=reset;
$('mode').onchange=()=>{reset();const cue=$('mode').value==='cue';$('cueCard').hidden=!cue;document.querySelectorAll('.cueOnly').forEach(e=>e.hidden=!cue);document.querySelectorAll('[data-prompt]').forEach(e=>{if(!e.classList.contains('cueOnly')&&!e.dataset.prompt.includes('Take your time'))e.hidden=cue});$('modeHelp').textContent=cue?'Illustrative retrieval rules with session history. Not a trained or validated aphasia model.':'Uses the dialogue provider configured on the server.';log('mode-change',{mode:$('mode').value})};
for(const [id,unit] of [['rate',' wpm'],['pause',' ms'],['gain','×'],['hesitation',' ms']])$(id).oninput=()=>{$(id+'Value').textContent=$(id).value+unit;if(id==='gain')controls();if(id==='hesitation')renderPauseEditor()};
for(let i=0;i<6;i++){const label=document.createElement('label');label.textContent='Weight '+(i+1);const input=document.createElement('input');input.type='range';input.min='-0.2';input.max='0.2';input.step='0.01';input.value='0';input.className='coefficient';input.setAttribute('aria-label','Mouth deformation weight offset '+(i+1));input.oninput=controls;$('coefficients').append(label,input)}
function controls(){send({type:'controls',controls:{gain:+$('gain').value,offsets:[...document.querySelectorAll('.coefficient')].map(e=>+e.value)}})}
$('neutral').onclick=()=>{document.querySelectorAll('.coefficient').forEach(e=>e.value=0);controls()};
$('likeness').onchange=()=>{cancel('Changing portrait');send({type:'avatar',asset:$('likeness').value});log('sample-change',{sample:$('likeness').value});$('phase').textContent='Ready to listen'};
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({prototype:'VOICE Avatar Lab V2',clinical_validation:false,events},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='voice-v2-session.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
$('mic').onclick=async()=>{
 if(recorder?.state==='recording'){recorder.stop();return}
 const token=cancel('Listening');
 try{send({type:'unlock'});stream=await navigator.mediaDevices.getUserMedia({audio:true});if(token!==epoch){stream.getTracks().forEach(t=>t.stop());return}chunks=[];recorder=new MediaRecorder(stream);recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
  recorder.onstop=async()=>{clearTimeout(recordTimer);stream.getTracks().forEach(t=>t.stop());$('mic').textContent='Record';if(token!==epoch)return;setBusy(true);$('phase').textContent='Transcribing';notice('Transcribing on this Mac…');try{const r=await fetch('/api/transcribe',{method:'POST',body:new Blob(chunks,{type:recorder.mimeType})});const d=await r.json();if(!r.ok)throw Error(d.error);if(token!==epoch)return;$('prompt').value=d.text;notice(d.text?'Review the transcript, then press Send.':'No speech detected. Try again.');log('transcription',{text:d.text})}catch(e){if(token===epoch)notice(e.message)}finally{if(token===epoch){setBusy(false);$('phase').textContent='Ready to listen'}}};
  recorder.start();setBusy(true);$('mic').disabled=false;$('mic').textContent='Finish';$('send').disabled=true;document.querySelectorAll('[data-prompt]').forEach(b=>b.disabled=true);notice('Recording. Click Finish when done (maximum 30 seconds).');recordTimer=setTimeout(()=>{if(recorder?.state==='recording')recorder.stop()},30000);
 }catch(e){if(token===epoch){notice('Microphone: '+e.message);$('phase').textContent='Ready to listen'}}
};
async function status(){try{const d=await(await fetch('/api/status')).json();sampleMode=!!d.sample_mode;
 $('systemStatus').textContent=d.error?'Model error':sampleMode?'Recorded example mode':d.llm&&d.asr?(d.dialogue_provider==='openai_compatible'?'AI services ready':'Local models ready'):'Loading models…';
 if(d.error)notice(d.error);
 const opt=$('backend').querySelector('[value=qwen3]');opt.disabled=!d.neural_available;opt.textContent=d.neural_available?'Qwen3-TTS · neural voice':'Qwen3-TTS · unavailable';
 if(sampleMode){const link=document.querySelector('.expression-entry .lab-link');link.removeAttribute('href');link.textContent='Expression Lab requires the full installation';$('backend').value='system';$('backend').disabled=true;$('backend').options[0].textContent='Recorded example audio';$('voice').disabled=true;$('mic').disabled=true;$('rate').disabled=true;$('pause').disabled=true;$('profile').disabled=true;$('rhythm').value='planned';$('rhythm').disabled=true;$('testVoice').hidden=true;$('backendHelp').textContent='Fixed synthetic replies and audio. Edit phrases and pause timing without loading language or speech models.';notice('Sample mode: try Interests, Offer a drink, or the Word-finding example. Replies are scripted.');}
 if(!d.error&&(!d.llm||(!sampleMode&&!d.asr)))setTimeout(status,1500)
 }catch{setTimeout(status,2000)}}status();setBusy(false);
$('voiceTurn').onchange=async e=>{const file=e.target.files[0];if(!file)return;const token=cancel('Preparing imported audio');send({type:'unlock'});setBusy(true);try{if(!ready)throw Error('Wait for the portrait to load.');if(file.size>6_000_000)throw Error('Turn file too large.');const d=await api('/api/voice-turn',JSON.parse(await file.text()));if(token!==epoch)return;message('assistant',d.text||'[Imported VOICE audio]');log('imported-voice-turn',{turnIndex:d.turnIndex,unmappedControls:d.unmappedControls});showTimeline(d);send({type:'speak',audio:d.audio,id:token});notice('Imported PCM16 audio. Emotion/motion codes are recorded, not applied.')}catch(err){if(token===epoch)notice(err.message)}finally{if(token===epoch)setBusy(false);e.target.value=''}};
$('testVoice').onclick=async()=>{if(busy)return;if(!ready){notice('Wait for the portrait to load.');return}const token=cancel('Preparing test');send({type:'unlock'});setBusy(true);try{await speak($('rhythm').value==='natural'?'Hello. I would like a cup of tea.':'I enjoy gardening... and... um... drinking tea.',token)}catch(e){if(token===epoch){notice(e.message);$('phase').textContent='Ready to retry'}}finally{if(token===epoch)setBusy(false)}};
function updateBackend(){renderPauseEditor();const neural=$('backend').value==='qwen3';$('hesitation').disabled=$('rhythm').value==='natural';$('neuralOptions').hidden=!neural;$('systemOptions').hidden=neural;$('backendHelp').textContent=neural?'Generated on this Mac. Preparation can take several seconds per fragment; repeats are cached in memory.':'Local system speech with exact inserted pauses.';$('pause').disabled=neural||$('rhythm').value!=='natural'}
$('backend').onchange=updateBackend;$('rhythm').onchange=updateBackend;updateBackend();
$('preset').onclick=()=>{if(sampleMode){location.reload();return}reset();$('backend').value='system';$('neuralVoice').value='Aiden';$('delivery').value='neutral';$('voice').value='Daniel';$('rate').value=160;$('pause').value=150;$('gain').value=1;$('rateValue').textContent='160 wpm';$('pauseValue').textContent='150 ms';$('gainValue').textContent='1.0×';$('profile').value='wordfinding';$('rhythm').value='planned';$('hesitation').value=700;$('hesitationValue').textContent='700 ms';$('mode').value='chat';$('mode').dispatchEvent(new Event('change'));$('likeness').value='assets';$('likeness').dispatchEvent(new Event('change'));document.querySelectorAll('.coefficient').forEach(e=>e.value=0);controls();$('idleMode').value='gentle';$('idleSpeed').value=.45;idleControls();updateBackend();notice('V2 defaults restored.')};
function toggleSettings(open){$('settingsPanel').hidden=!open;$('settingsToggle').setAttribute('aria-expanded',String(open));if(open)$('closeSettings').focus();else $('settingsToggle').focus()}
$('settingsToggle').onclick=()=>toggleSettings($('settingsPanel').hidden);$('closeSettings').onclick=()=>toggleSettings(false);document.addEventListener('keydown',e=>{if(e.key==='Escape')toggleSettings(false)});
function idleControls(){const mode=$('idleMode').value,speed=+$('idleSpeed').value;$('idleSpeedValue').textContent=speed.toFixed(2)+'×';$('idleSpeed').disabled=mode!=='gentle';send({type:'idle',mode,speed});log('idle-controls',{mode,speed})}
$('idleMode').onchange=idleControls;$('idleSpeed').oninput=idleControls;
