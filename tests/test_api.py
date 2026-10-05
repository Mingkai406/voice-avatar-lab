import importlib,json,os,sys,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(os.environ,{'AVATAR_SAMPLE_MODE':'1'}):
            from avatar_lab import server
            cls.module=importlib.reload(server);cls.module.initialize()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),cls.module.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def call(self,path,data=None,headers=None):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data else None,headers=headers or {})
        with urllib.request.urlopen(req,timeout=10) as r:return json.load(r)
    def test_roundtrip(self):
        status=self.call('/api/status');self.assertTrue(status['sample_mode']);self.assertEqual(status['dialogue_provider'],'fixtures')
        reply=self.call('/api/chat',{'prompt':'What do you enjoy?','profile':'wordfinding'})
        audio=self.call('/api/say',{'text':reply['text'],'plan':reply['plan'],'rhythm':'planned'})
        self.assertGreater(audio['duration'],0);self.assertEqual(len(audio['segments']),3)
    def test_cross_origin_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.call('/api/chat',{'prompt':'hello'},{'Origin':'https://example.invalid'})
        self.assertEqual(ctx.exception.code,403)
    def test_sample_expression_unavailable(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.call('/api/portrait',{'smile':1})
        self.assertEqual(ctx.exception.code,400)
    def test_root_serves_only_public_files(self):
        with urllib.request.urlopen(self.base+'/') as r:self.assertIn(b'VOICE',r.read())
        with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(self.base+'/.env')
if __name__=='__main__':unittest.main()
