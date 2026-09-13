"""Actual file/receipt/PE/transaction functions, with explicit temporary filesystem fixtures."""
from __future__ import annotations
import json,shutil,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import product as p
import install_candidate as inst
from release_archive import write_sums
from build_candidate import gather_receipt
from binary_utils import FormatError
class ProductTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def fixture(self):
  root=self.base/'source';game=self.base/'game';(root/'payload').mkdir(parents=True);(game/'data').mkdir(parents=True)
  for name,rel in inst.MANAGED.items():
   shutil.copy2(p.ROOT/'baseline'/name,game/rel);(root/'payload'/name).write_bytes(b'NEW_CANDIDATE_'+name.encode())
  expect={name:p.file_hash(root/'payload'/name) for name in inst.MANAGED};return root,game,self.base/'backup',expect
 def test_baseline_all_hashes(self):self.assertEqual(len(p.verify_baseline()),4)
 def test_sixteen_guard_bytes_and_pack(self):self.assertEqual(p.verify_sources()['guards'],16)
 def test_pack_roundtrip(self):self.assertEqual(p.unpack(p.pack(b'return "text"')),b'return "text"')
 def test_pack_truncation_refused(self):
  with self.assertRaises(FormatError):p.unpack(p.pack(b'x')[:-1])
 def test_pack_extra_bytes_refused(self):
  with self.assertRaises(FormatError):p.unpack(p.pack(b'x')+b'x')
 def test_pack_wrong_path_refused(self):
  with self.assertRaises(FormatError):p.unpack(p.pack(b'x').replace(b'queue_probe.lua',b'other_probe.lua'))
 def test_baseline_dll_real_export(self):
  pe=p.PE((p.ROOT/'baseline/wh3_native_bridge.dll').read_bytes());self.assertTrue(p.require_exports(pe,['luaopen_wh3_native_bridge']))
 def test_minhook_real_exports(self):self.assertTrue(p.require_exports(p.PE((p.ROOT/'baseline/minhook.x64.dll').read_bytes()),p.BACKEND_EXPORTS))
 def test_nonexistent_export_refused(self):
  with self.assertRaises(FormatError):p.require_exports(p.PE((p.ROOT/'baseline/minhook.x64.dll').read_bytes()),['invented_export'])
 def test_invalid_pe_refused(self):
  with self.assertRaises(FormatError):p.PE(b'not a PE file')
 def test_pe_rva_outside_refused(self):
  pe=p.PE((p.ROOT/'baseline/minhook.x64.dll').read_bytes())
  with self.assertRaises(FormatError):pe.at(0xfffffff0,100)
 def test_old_dll_cannot_be_candidate(self):
  with self.assertRaises(FormatError):p.verify_candidate_pe(p.ROOT/'baseline/wh3_native_bridge.dll')
 def test_wrong_game_refuses_before_rvas(self):
  f=self.base/'Warhammer3.exe';f.write_bytes(b'not locked game')
  with self.assertRaisesRegex(FormatError,'SHA256'):p.preflight(f)
 def test_lua_ids_not_numerified(self):
  s=(p.ROOT/'lua/queue_probe.lua').read_text();self.assertNotIn('tonumber(',s);self.assertNotIn('rawget(_G',s.replace('-- Direct global lookup follows that environment; rawget(_G, ...) may bypass it.',''))
 def test_client_no_auto_issue(self):
  s=(p.ROOT/'lua/queue_probe.lua').read_text();self.assertNotIn('bridge.arm_verified_issue(',s);self.assertNotIn('bridge.issue_verified_command(',s)
 def test_code_hash_ignores_output_not_source(self):
  r=self.base/'r';(r/'src').mkdir(parents=True);(r/'src/a.cpp').write_text('1');first=p.code_digest(r)
  (r/'output').mkdir();(r/'output/cache').write_text('x');self.assertEqual(first,p.code_digest(r));(r/'src/a.cpp').write_text('2');self.assertNotEqual(first,p.code_digest(r))
 def test_checksum_manifest(self):
  r=self.base/'r';r.mkdir();(r/'a').write_bytes(b'A');self.assertEqual(write_sums(r),1);self.assertEqual(p.verify_sums(r),1)
 def test_checksum_changed_file(self):
  r=self.base/'r';r.mkdir();(r/'a').write_bytes(b'A');write_sums(r);(r/'a').write_bytes(b'B')
  with self.assertRaises(FormatError):p.verify_sums(r)
 def test_checksum_path_traversal_refused(self):
  (self.base/'SHA256SUMS.txt').write_text('0'*64+'  ../escape\n')
  with self.assertRaises(FormatError):p.verify_sums(self.base)
 def test_zip_deterministic(self):
  r=self.base/'r';r.mkdir();(r/'a').write_bytes(b'A');z1=self.base/'1.zip';z2=self.base/'2.zip';p.zip_tree(r,z1);p.zip_tree(r,z2);self.assertEqual(z1.read_bytes(),z2.read_bytes())
 def test_zip_traversal_refused(self):
  z=self.base/'x.zip'
  with zipfile.ZipFile(z,'w') as f:f.writestr('../escape',b'x')
  with self.assertRaises(FormatError):p.safe_extract(z,self.base/'extract')
 def test_zip_duplicate_refused(self):
  z=self.base/'x.zip'
  with zipfile.ZipFile(z,'w') as f:f.writestr('same',b'1');f.writestr('same',b'2')
  with self.assertRaises(FormatError):p.safe_extract(z,self.base/'extract')
 def test_fake_windows_receipt_refused(self):
  with self.assertRaises(FormatError):gather_receipt({'status':'PASS','windows_dll_built':False},{'status':'PASS'},self.base/'none')
 def test_stale_build_receipt_refused(self):
  with self.assertRaisesRegex(FormatError,'different source'):gather_receipt({'status':'PASS','windows_dll_built':True,'windows_private_process_smoke':True,'source_digest':'bad'},{'status':'PASS'},self.base/'none')
 def test_install_only_two_files_and_backup(self):
  r,g,b,e=self.fixture();(g/'Warhammer3.exe').write_bytes(b'untouched');m=inst.install_transaction(r,g,b,e);self.assertEqual(m['state'],'INSTALLED');self.assertEqual((g/'Warhammer3.exe').read_bytes(),b'untouched')
  for n,rel in inst.MANAGED.items():self.assertEqual(p.file_hash(b/n),p.BASELINE_HASHES[n]);self.assertEqual(p.file_hash(g/rel),e[n])
 def test_changed_baseline_refused(self):
  r,g,b,e=self.fixture();(g/'wh3_native_bridge.dll').write_bytes(b'other mod')
  with self.assertRaises(FormatError):inst.install_transaction(r,g,b,e)
  self.assertFalse(b.exists())
 def test_transaction_failure_rolls_back(self):
  r,g,b,e=self.fixture();original=inst.atomic_copy;calls=[0]
  def fail_second(s,d):
   calls[0]+=1
   if calls[0]==2:raise OSError('injected disk failure')
   original(s,d)
  with patch.object(inst,'atomic_copy',side_effect=fail_second):
   with self.assertRaises(OSError):inst.install_transaction(r,g,b,e)
  for n,rel in inst.MANAGED.items():self.assertEqual(p.file_hash(g/rel),p.BASELINE_HASHES[n])
 def test_changed_candidate_rolls_back(self):
  r,g,b,e=self.fixture();e['zzz_queue_probe.pack']='0'*64
  with self.assertRaises(FormatError):inst.install_transaction(r,g,b,e)
  for n,rel in inst.MANAGED.items():self.assertEqual(p.file_hash(g/rel),p.BASELINE_HASHES[n])
 def test_normal_rollback(self):
  r,g,b,e=self.fixture();inst.install_transaction(r,g,b,e);self.assertEqual(inst.rollback_transaction(b,g)['state'],'ROLLED_BACK')
  for n,rel in inst.MANAGED.items():self.assertEqual(p.file_hash(g/rel),p.BASELINE_HASHES[n])
 def test_rollback_preserves_third_party_change(self):
  r,g,b,e=self.fixture();inst.install_transaction(r,g,b,e);(g/'wh3_native_bridge.dll').write_bytes(b'other writer')
  with self.assertRaises(FormatError):inst.rollback_transaction(b,g)
  self.assertEqual((g/'wh3_native_bridge.dll').read_bytes(),b'other writer')
 def test_rollback_wrong_game_refused(self):
  r,g,b,e=self.fixture();inst.install_transaction(r,g,b,e)
  with self.assertRaises(FormatError):inst.rollback_transaction(b,self.base/'different_game')
 def test_rollback_tampered_backup_refused(self):
  r,g,b,e=self.fixture();inst.install_transaction(r,g,b,e);(b/'wh3_native_bridge.dll').write_bytes(b'bad')
  with self.assertRaises(FormatError):inst.rollback_transaction(b,g)
 def test_mention_or_commented_carrier_does_not_count_as_enabled(self):
  self.assertFalse(inst.is_carrier_enabled('// mod "zzz_queue_probe.pack";'))
  self.assertFalse(inst.is_carrier_enabled('/*\nmod "zzz_queue_probe.pack";\n*/'))
  self.assertFalse(inst.is_carrier_enabled('mod "zzz_queue_probe.pack.disabled";'))
  self.assertTrue(inst.is_carrier_enabled('mod "zzz_queue_probe.pack";'))
 def test_source_archive_without_receipt_is_not_installable(self):
  with patch.object(inst,'verify_sums',return_value=0),patch.object(inst,'verify_sources',return_value={}):
   with self.assertRaisesRegex(FormatError,'SOURCE ZIP IS NOT INSTALLABLE'):inst.candidate_check(self.base,self.base/'game')
 def test_default_native_issue_build_is_off(self):self.assertIn('NEVER release-approved" OFF)',(p.ROOT/'CMakeLists.txt').read_text())
 def test_real_packet_handlers_are_guarded_and_wired(self):
  profile=json.loads((p.ROOT/'evidence/native_profile.json').read_text());rvas=[g['rva'] for g in profile['guards']]
  self.assertIn(0x2D95A50,rvas);self.assertIn(0x2D95F8C,rvas)
  win=(p.ROOT/'src/platform_windows.cpp').read_text()
  self.assertIn('move_handler_hook',win);self.assertIn('attack_handler_hook',win)
  self.assertIn('std::array<void*,16>',win);self.assertIn('NativePacketHandlerFn>(tramp[12])',win);self.assertIn('NativePacketHandlerFn>(tramp[13])',win)
if __name__=='__main__':unittest.main(verbosity=2)
