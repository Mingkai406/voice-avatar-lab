"""Normalized boundary for a VOICE turn. Does not access production services."""
import base64,io,wave

def normalize_turn(data):
 if data.get('format')!='pcm_16000':raise ValueError('Expected mono signed PCM16 little-endian, format pcm_16000.')
 pcm=base64.b64decode(data.get('audioBase64',''),validate=True)
 if not pcm or len(pcm)%2 or len(pcm)>32000*120:raise ValueError('PCM must be nonempty, even-length, and at most 120 seconds.')
 buf=io.BytesIO()
 with wave.open(buf,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(pcm)
 return {'audio':base64.b64encode(buf.getvalue()).decode(),'text':str(data.get('responseText',''))[:2000], 'turnIndex':data.get('turnIndex'), 'duration':len(pcm)/32000,'emotionCode':data.get('emotionCode'),'motionCode':data.get('motionCode'),'unmappedControls':['emotionCode','motionCode']}
