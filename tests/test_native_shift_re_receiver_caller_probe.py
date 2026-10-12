"""Static contract: native receiver caller origin, no default game mutation."""
import unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"
class ReceiverCallerProbeTests(unittest.TestCase):
 def test_exact_original_two_guarded_entrypoints(self):
  js=(SRC/"receiver_caller_one_shot.js").read_text(encoding="utf8")
  self.assertIn("[0x0306b9f0,'48895c2410']",js)
  self.assertIn("[0x0306ba5b,'e8683defff']",js)
  self.assertIn("this.returnAddress",js)
  self.assertIn("callerReturnRva",js)
  self.assertIn("matchedReceiverFrame",js)
  self.assertLess(js.index("for(const [rva,expected] of pins)"),
                  js.index("Interceptor.attach("))
 def test_no_gameplay_mutation(self):
  js=(SRC/"receiver_caller_one_shot.js").read_text(encoding="utf8")
  self.assertNotIn("writePointer(",js)
  self.assertNotIn("WriteProcessMemory",js)
  self.assertIn("max=200",js)
if __name__=="__main__":unittest.main()
