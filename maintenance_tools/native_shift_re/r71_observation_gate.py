"""Offline-only R71 safety-contract; passing never authorizes injection."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Gate:
    same_sha:bool=False
    stolen_instructions:bool=False
    thread_identity:bool=False
    member_lifetime:bool=False
    full_register_and_flags:bool=False
    x64_unwind_preserved:bool=False
    no_hook_collision:bool=False
    reversible_install:bool=False
    bounded_noalloc_publish:bool=False
    memory_order:bool=False
    member_generation:bool=False
    world_goal_ref_lifetime:bool=False
    private_windows_validation:bool=False
    def evaluate(self):
        return {'missing':[k for k,v in self.__dict__.items() if not v],
                'ready_for_design_review':all(self.__dict__.values()),
                'live_hook_authorized':False,'gameplay_patch_authorized':False}
