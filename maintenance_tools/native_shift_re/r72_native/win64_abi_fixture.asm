; R72 Windows x64 test fixture. Not a detour, cave, stolen instruction replay, or WH3 hook.
; PUBLIC function bsc_win64_roundtrip(RCX=Event*, RDX=marker*) -> int.
; RFLAGS check is scoped to the pre-callback window (NOT caller-entry flags).
; Fully owned, compiler-independent synthetic frame with native UNWIND metadata.
OPTION CASEMAP:NONE
EXTERN bsc_fixture_callback:PROC
PUBLIC bsc_win64_roundtrip
PUBLIC bsc_win64_verify_sentinel
.data
ALIGN 16
r72_xmm_sentinel DQ 0123456789ABCDEFh, 0FEDCBA9876543210h
.code
bsc_win64_roundtrip PROC FRAME
    push rbx
    .pushreg rbx
    push rsi
    .pushreg rsi
    push rdi
    .pushreg rdi
    push r12
    .pushreg r12
    sub rsp, 0D8h
    .allocstack 0D8h
    movaps xmmword ptr [rsp+020h], xmm6
    .savexmm128 xmm6, 020h
    movaps xmmword ptr [rsp+030h], xmm7
    .savexmm128 xmm7, 030h
    movaps xmmword ptr [rsp+040h], xmm8
    .savexmm128 xmm8, 040h
    movaps xmmword ptr [rsp+050h], xmm9
    .savexmm128 xmm9, 050h
    movaps xmmword ptr [rsp+060h], xmm10
    .savexmm128 xmm10, 060h
    movaps xmmword ptr [rsp+070h], xmm11
    .savexmm128 xmm11, 070h
    movaps xmmword ptr [rsp+080h], xmm12
    .savexmm128 xmm12, 080h
    movaps xmmword ptr [rsp+090h], xmm13
    .savexmm128 xmm13, 090h
    movaps xmmword ptr [rsp+0A0h], xmm14
    .savexmm128 xmm14, 0A0h
    movaps xmmword ptr [rsp+0B0h], xmm15
    .savexmm128 xmm15, 0B0h
    .endprolog
    ; Shadow space is [rsp..rsp+01Fh]. Save flags in dedicated [rsp+0C0h].
    stc
    pushfq
    pop rax
    mov qword ptr [rsp+0C0h], rax
    call bsc_fixture_callback
    mov rax, qword ptr [rsp+0C0h]
    push rax
    popfq
    setc al
    movzx eax, al
    movaps xmm6, xmmword ptr [rsp+020h]
    movaps xmm7, xmmword ptr [rsp+030h]
    movaps xmm8, xmmword ptr [rsp+040h]
    movaps xmm9, xmmword ptr [rsp+050h]
    movaps xmm10, xmmword ptr [rsp+060h]
    movaps xmm11, xmmword ptr [rsp+070h]
    movaps xmm12, xmmword ptr [rsp+080h]
    movaps xmm13, xmmword ptr [rsp+090h]
    movaps xmm14, xmmword ptr [rsp+0A0h]
    movaps xmm15, xmmword ptr [rsp+0B0h]
    add rsp, 0D8h
    pop r12
    pop rdi
    pop rsi
    pop rbx
    ret
bsc_win64_roundtrip ENDP

; Caller-side contract fixture: check controlled callback-window CF, RBX, R12, XMM6 intact.
; This tests normal Win64 ABI only; a live mid-function detour has additional volatile state.
bsc_win64_verify_sentinel PROC FRAME
    push rbx
    .pushreg rbx
    push r12
    .pushreg r12
    sub rsp, 038h
    .allocstack 038h
    movaps xmmword ptr [rsp+020h], xmm6
    .savexmm128 xmm6, 020h
    .endprolog
    mov rbx, 1122334455667788h
    mov r12, 9988776655443322h
    movdqa xmm6, xmmword ptr [r72_xmm_sentinel]
    call bsc_win64_roundtrip
    cmp eax, 1
    jne r72_fail
    mov rax, 1122334455667788h
    cmp rbx, rax
    jne r72_fail
    mov rax, 9988776655443322h
    cmp r12, rax
    jne r72_fail
    movdqa xmm0, xmmword ptr [r72_xmm_sentinel]
    pcmpeqb xmm0, xmm6
    pmovmskb eax, xmm0
    cmp eax, 0FFFFh
    jne r72_fail
    mov eax, 1
    jmp r72_done
r72_fail:
    xor eax, eax
r72_done:
    movaps xmm6, xmmword ptr [rsp+020h]
    add rsp, 038h
    pop r12
    pop rbx
    ret
bsc_win64_verify_sentinel ENDP
END
