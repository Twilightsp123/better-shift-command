import importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('ev',ROOT/'tools/experimental_validation.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
from binary_utils import unpack
from product import file_hash
class GameValidationToolTests(unittest.TestCase):
 def test_validation_pack_matches_lua(self):
  self.assertEqual(unpack((ROOT/'dist/zzz_queue_probe_validation.pack').read_bytes()),(ROOT/'game_validation/queue_probe_validation.lua').read_bytes())
  text=(ROOT/'game_validation/queue_probe_validation.lua').read_text()
  for s in ['OUR_CONTROLLER','REJECTED_STALE','PLAYER_RMB_PASS','VALIDATION_PASS','experimental_issue_armed']:
   self.assertIn(s,text)
 def test_locate_manifest_rejects_stale_unlocked_candidate(self):
  current={'experimental_issue_build':True,'version':ev.VERSION,'source_digest':ev.code_digest(ev.ROOT),'windows_build':'PASS','windows_private_process_smoke':'PASS'}
  self.assertTrue(ev.candidate_manifest_matches_current(current))
  stale=dict(current);stale['version']='0.4.1-guarded-adapter'
  self.assertFalse(ev.candidate_manifest_matches_current(stale))
  stale=dict(current);stale['source_digest']='0'*64
  self.assertFalse(ev.candidate_manifest_matches_current(stale))
  stale=dict(current);stale['experimental_issue_build']=False
  self.assertFalse(ev.candidate_manifest_matches_current(stale))
 def test_collect_then_rollback(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);game=t/'game';(game/'data').mkdir(parents=True);backup=t/'backup';backup.mkdir();out=t/'out';work=t/'kit';(work/'game_validation').mkdir(parents=True)
   olds={'wh3_native_bridge.dll':b'old-dll','zzz_queue_probe.pack':b'old-pack'};news={'wh3_native_bridge.dll':b'new-dll','zzz_queue_probe.pack':b'new-pack'}
   for n,b in olds.items():(backup/n).write_bytes(b)
   (game/'wh3_native_bridge.dll').write_bytes(news['wh3_native_bridge.dll']);(game/'data/zzz_queue_probe.pack').write_bytes(news['zzz_queue_probe.pack'])
   state={'game_root':str(game.resolve()),'backup':str(backup.resolve()),'candidate_zip_sha256':'abc','candidate_manifest':{'experimental_issue_build':True},'state':'INSTALLED_FOR_ONE_GAME_VALIDATION','files':[{'relative':'wh3_native_bridge.dll','backup':'wh3_native_bridge.dll','old_sha256':file_hash(backup/'wh3_native_bridge.dll')},{'relative':'data/zzz_queue_probe.pack','backup':'zzz_queue_probe.pack','old_sha256':file_hash(backup/'zzz_queue_probe.pack')}],'installed_sha256':{'wh3_native_bridge.dll':file_hash(game/'wh3_native_bridge.dll'),'zzz_queue_probe.pack':file_hash(game/'data/zzz_queue_probe.pack')}}
   oldroot,oldstate=ev.ROOT,ev.STATE;ev.ROOT=work;ev.STATE=work/'game_validation/last_install_state.json';ev.STATE.write_text(json.dumps(state))
   try:
    log=t/'script_log_test.txt';lines=[b'[BRIDGE_GAMEVAL_V050] '+x for x in ev.REQUIRED];log.write_bytes(b'\n'.join(lines)+b'\n')
    z,summary=ev.collect_and_rollback(log,out);self.assertTrue(summary['validation_pass']);self.assertTrue(z.is_file())
    self.assertEqual((game/'wh3_native_bridge.dll').read_bytes(),olds['wh3_native_bridge.dll']);self.assertEqual((game/'data/zzz_queue_probe.pack').read_bytes(),olds['zzz_queue_probe.pack'])
    with zipfile.ZipFile(z) as zz:self.assertIn('VALIDATION_RESULT.json',zz.namelist())
   finally:ev.ROOT,ev.STATE=oldroot,oldstate
if __name__=='__main__':unittest.main()
