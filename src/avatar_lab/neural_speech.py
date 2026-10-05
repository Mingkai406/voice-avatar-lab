"""Keep new speech dependencies isolated from the working demo environment."""
import atexit, base64, io, json, os, select, subprocess, threading, time, wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
_process=None
_lock=threading.Lock()
_cache={}

def available():
    return (ROOT/'.venv-tts/bin/python').exists() and (ROOT/'models/qwen3-tts/model.safetensors').exists()

def close():
    global _process
    if _process is not None:
        _process.terminate()
        try:_process.wait(timeout=3)
        except subprocess.TimeoutExpired:_process.kill()
        _process=None
atexit.register(close)

def synthesize(data):
    global _process
    text=str(data.get('text','')).strip()[:1000]
    if not text:raise ValueError('Nothing to speak.')
    if not available():raise ValueError('Neural voice is not installed. Choose System voice.')
    request={'text':text,'speaker':data.get('neural_voice','Aiden'),'delivery':data.get('delivery','neutral')}
    if request['speaker'] not in ['Aiden','Ryan']:request['speaker']='Aiden'
    key=json.dumps(request,sort_keys=True)
    start=time.perf_counter()
    with _lock:
        if key in _cache:
            result={**_cache[key],'cached':True,'generation_s':0}
        else:
            if _process is None or _process.poll() is not None:
                _process=subprocess.Popen([str(ROOT/'.venv-tts/bin/python'),str(ROOT/'src/avatar_lab/neural_speech_worker.py')],
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,
                    env={**os.environ,'HF_HUB_OFFLINE':'1'},cwd=str(ROOT))
            _process.stdin.write(json.dumps(request)+'\n');_process.stdin.flush()
            if not select.select([_process.stdout],[],[],150)[0]:
                close();raise ValueError('Neural speech timed out. Choose System voice for a faster response.')
            line=_process.stdout.readline()
            if not line:close();raise ValueError('Neural voice stopped. Choose System voice or try again.')
            result=json.loads(line)
            if result.get('error'):raise ValueError('Neural voice: '+result['error'])
            if len(_cache)>=64:_cache.pop(next(iter(_cache)))
            _cache[key]=result.copy()
            result['cached']=False
    # The rate slider changes waveform timing, independently of style instructions.
    rate=max(20,min(220,int(float(data.get('rate',160)))))
    if rate!=160:
        import imageio_ffmpeg
        factor=rate/160;filters=[]
        while factor<.5:filters.append('atempo=0.5');factor/=.5
        filters.append(f'atempo={factor:.6f}')
        out=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-v','error','-i','pipe:0',
            '-af',','.join(filters),'-f','s16le','-ac','1','-ar','16000','pipe:1'],
            input=base64.b64decode(result['audio']),capture_output=True,check=True,timeout=45).stdout
        b=io.BytesIO()
        with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(out)
        result={**result,'audio':base64.b64encode(b.getvalue()).decode(),'duration':len(out)/32000}
    return {**result,'rate':rate,'pause':0,'request_s':round(time.perf_counter()-start,3)}
