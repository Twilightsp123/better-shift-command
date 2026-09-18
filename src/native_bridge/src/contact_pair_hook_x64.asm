; Windows x64 mid-function contact-pair observer stub.
; Hook site: Warhammer3.exe+0x2F68C35, after contact/intersection branches.
; This is NOT a normal function entry. Preserve all volatile GPRs, RFLAGS and
; volatile XMM registers before calling the C observer, then continue through
; MinHook's relocated trampoline.

EXTERN wh3_contact_pair_observer:PROC
EXTERN g_wh3_contact_pair_trampoline:QWORD
PUBLIC wh3_contact_pair_detour_stub

.code
wh3_contact_pair_detour_stub PROC
    pushfq
    push rax
    push rcx
    push rdx
    push r8
    push r9
    push r10
    push r11

    ; The hook is in the middle of a native frame. Align dynamically rather
    ; than assuming the function's current stack parity. r11's original value
    ; is already saved above.
    mov r11, rsp
    and rsp, -16
    sub rsp, 090h                ; shadow space + XMM saves + saved pre-align rsp
    mov qword ptr [rsp+080h], r11

    movdqu xmmword ptr [rsp+020h], xmm0
    movdqu xmmword ptr [rsp+030h], xmm1
    movdqu xmmword ptr [rsp+040h], xmm2
    movdqu xmmword ptr [rsp+050h], xmm3
    movdqu xmmword ptr [rsp+060h], xmm4
    movdqu xmmword ptr [rsp+070h], xmm5

    mov rcx, rdi                 ; ResultRecord* proven by RE08
    call wh3_contact_pair_observer

    movdqu xmm0, xmmword ptr [rsp+020h]
    movdqu xmm1, xmmword ptr [rsp+030h]
    movdqu xmm2, xmmword ptr [rsp+040h]
    movdqu xmm3, xmmword ptr [rsp+050h]
    movdqu xmm4, xmmword ptr [rsp+060h]
    movdqu xmm5, xmmword ptr [rsp+070h]

    mov rsp, qword ptr [rsp+080h]
    pop r11
    pop r10
    pop r9
    pop r8
    pop rdx
    pop rcx
    pop rax
    popfq
    jmp qword ptr [g_wh3_contact_pair_trampoline]
wh3_contact_pair_detour_stub ENDP
END
