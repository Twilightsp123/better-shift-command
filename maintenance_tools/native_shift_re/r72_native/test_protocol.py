import unittest
from interpret_capture import interpret,SCHEMA

def row(**kw):
    e=dict(member_token=123,owner_epoch=9,tick_sequence=4,thread_tag=2,phase=1,x_bits=7,z_bits=10)
    e.update(kw)
    return e

class Contract(unittest.TestCase):
    def test_one_track(self):
        x=interpret(dict(schema=SCHEMA,events=[row(),row(tick_sequence=5)]))
        self.assertEqual(x['local_tracks'],1)
        self.assertFalse(x['cross_member_atomicity'])
    def test_multimember_not_atomic(self):
        x=interpret(dict(schema=SCHEMA,events=[row(),row(member_token=124)]))
        self.assertEqual(x['local_tracks'],2)
        self.assertFalse(x['gameplay_root_cause_proven'])
    def test_per_thread_separate(self):
        self.assertEqual(interpret(dict(schema=SCHEMA,events=[row(),row(thread_tag=3)]))['local_tracks'],2)
    def test_epoch_split(self):
        self.assertEqual(interpret(dict(schema=SCHEMA,events=[row(),row(owner_epoch=10)]))['local_tracks'],2)
    def test_reject_schema(self):
        with self.assertRaisesRegex(ValueError,'SCHEMA'):interpret({'events':[]})
    def test_reject_negative(self):
        with self.assertRaisesRegex(ValueError,'VALUE'):interpret(dict(schema=SCHEMA,events=[row(phase=-1)]))
    def test_reject_bool(self):
        with self.assertRaisesRegex(ValueError,'VALUE'):interpret(dict(schema=SCHEMA,events=[row(thread_tag=True)]))
    def test_reject_pointer_like_extraneous(self):
        with self.assertRaisesRegex(ValueError,'FIELDS'):interpret(dict(schema=SCHEMA,events=[row(raw_pointer=0xF0000)]))
    def test_reject_zero_token(self):
        with self.assertRaisesRegex(ValueError,'LIFETIME'):interpret(dict(schema=SCHEMA,events=[row(member_token=0)]))
    def test_reject_zero_epoch(self):
        with self.assertRaisesRegex(ValueError,'LIFETIME'):interpret(dict(schema=SCHEMA,events=[row(owner_epoch=0)]))
    def test_reject_disorder(self):
        with self.assertRaisesRegex(ValueError,'ORDER'):interpret(dict(schema=SCHEMA,events=[row(tick_sequence=5),row(tick_sequence=4)]))
    def test_reject_duplicate(self):
        with self.assertRaisesRegex(ValueError,'ORDER'):interpret(dict(schema=SCHEMA,events=[row(),row()]))
    def test_no_causal_claim(self):
        x=interpret(dict(schema=SCHEMA,events=[]))
        self.assertFalse(x['native_game_hook_authorized'])
        self.assertFalse(x['worker_lifetime_proven'])

if __name__=='__main__':unittest.main()
