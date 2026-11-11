import ast,hashlib,io,json,os,pathlib,subprocess,tarfile,tempfile,unittest
SOURCE=pathlib.Path(__file__).with_name('import_snapshots.py')
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
class SymlinkArchiveTests(unittest.TestCase):
 def execute(self,tmp,malicious=False):
  root=pathlib.Path(tmp)/'repo';root.mkdir();cache=pathlib.Path(tmp)/'cache';cache.mkdir();outside=pathlib.Path(tmp)/'external';outside.mkdir()
  link=str(outside);sha='1'*40;name='fixture';entries=[{'path':'safe.txt','mode':'100644','type':'blob','sha':blob(b'safe')},{'path':'LatestBuild','mode':'120000','type':'blob','sha':blob(link.encode())}]
  archive=cache/(name+'-'+sha+'.tar.gz')
  with tarfile.open(archive,'w:gz') as tar:
   m=tarfile.TarInfo('owner-fixture/LatestBuild');m.type=tarfile.SYMTYPE;m.linkname=link;tar.addfile(m)
   content=b'safe';m=tarfile.TarInfo('owner-fixture/safe.txt');m.size=len(content);tar.addfile(m,io.BytesIO(content))
   if malicious:
    m=tarfile.TarInfo('owner-fixture/LatestBuild/escaped.txt');m.size=4;tar.addfile(m,io.BytesIO(b'evil'))
  module=ast.parse(SOURCE.read_text());function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='import_one')
  scope=dict(ROOT=root,CACHE=cache,destinations={name:'collections/reverse/'+name},pathlib=pathlib,subprocess=subprocess,json=json,tarfile=tarfile,hashlib=hashlib,os=os)
  exec(compile(ast.Module(body=[function],type_ignores=[]),str(SOURCE),'exec'),scope)
  metadata=dict(name=name,id=1,fork=True,branch='master',sha=sha,parent='upstream/fixture',license=None,pages=False,description='test',files=2,bytes=4+len(link),tree=entries)
  if malicious:
   with self.assertRaises(RuntimeError):scope['import_one'](metadata)
   self.assertFalse((outside/'escaped.txt').exists());return
  try:scope['import_one'](metadata)
  except RuntimeError as e:self.fail('Historical symlink must be preserved without dereferencing: '+str(e))
  dest=root/'collections/reverse/fixture';self.assertEqual(os.readlink(dest/'LatestBuild'),link);self.assertEqual((dest/'safe.txt').read_bytes(),b'safe');self.assertEqual(list(outside.iterdir()),[])
 def test_preserves_historical_absolute_symlink_without_accessing_target(self):
  with tempfile.TemporaryDirectory() as tmp:self.execute(tmp)
 def test_rejects_archive_members_below_symlink_without_external_write(self):
  with tempfile.TemporaryDirectory() as tmp:self.execute(tmp,True)
if __name__=='__main__':unittest.main()
