import hashlib,json,os,pathlib,subprocess,tempfile,unittest
from unittest.mock import patch
class SelfCreatedSourceTests(unittest.TestCase):
 def test_self_created_source_has_no_parent_and_keeps_pages_compatibility(self):
  script=pathlib.Path(__file__).with_name('build_catalog.py').read_text()
  content=b'notes';sha=hashlib.sha1(b'blob 5\0'+content).hexdigest()
  source=dict(name='Learn-GCD',id=1,fork=False,branch='master',sha='2'*40,parent=None,license=None,pages=True,description='GCD',files=1,bytes=5,destination='collections/concurrency/Learn-GCD',source_url='https://github.com/476139183/Learn-GCD')
  inventory=[dict(name='LearningIOS',sha='1'*40),dict(source,tree=[dict(path='notes.txt',type='blob',mode='100644',sha=sha)])]
  fixtures={'/tmp/batch-sources-inventory.json':inventory,'/tmp/batch-import-manifest.json':[source],'/tmp/batch-history-manifest.json':[dict(name='Learn-GCD',tags={'refs/tags/legacy/Learn-GCD/branches/master':'2'*40})]}
  original_read=pathlib.Path.read_text
  def read(path,*args,**kwargs):
   if str(path) in fixtures:return json.dumps(fixtures[str(path)])
   return original_read(path,*args,**kwargs)
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);config=root/'scripts/cleanup-batch/config.json';config.parent.mkdir(parents=True)
   config.write_text(json.dumps(dict(target='LearningIOS',groups={'concurrency':['Learn-GCD']},retain_sources=['Learn-GCD'])))
   folder=root/source['destination'];folder.mkdir(parents=True);(folder/'notes.txt').write_bytes(content)
   with patch.dict(os.environ,KNOWLEDGE_ROOT=str(root)),patch.object(pathlib.Path,'read_text',read),patch.object(subprocess,'check_output',return_value=b'ORIGINAL INDEX'):
    try:exec(compile(script,'build_catalog.py','exec'),{'__name__':'migration_test'})
    except TypeError as e:self.fail('Self-created source without an upstream must render: '+str(e))
   page=(root/'catalog/Learn-GCD.md').read_text();manifest=json.loads((root/'catalog/manifest.json').read_text())
   self.assertIn('自建项目',page);self.assertEqual(manifest['sources'][0]['original_repository_status'],'retained_for_compatibility')
   self.assertNotIn('Learn-GCD',manifest['pending_cleanup']);self.assertTrue((root/'README.md').read_text().endswith('ORIGINAL INDEX'))
if __name__=='__main__':unittest.main()
