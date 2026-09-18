; Standalone fixture target function with an explicit mid-function hook site.
; Windows x64 ABI.

PUBLIC target_function_mid_hook
PUBLIC mid_hook_site_anchor
EXTERN test_mid_function_observer:PROC
EXTERN g_test_mid_function_trampoline:QWORD
PUBLIC test_mid_function_detour_stub

.code

; std::int64_t target_function_mid_hook(std::int64_t a, std::int64_t b, std::int64_t test_rdi_val)
; rcx = a, rdx = b, r8 = test_rdi_val
target_function_mid_hook PROC
    push rbp
    mov rbp, rsp
    push rbx
    push rsi
    push rdi
    push r12
    push r13
    push r14
    push r15
    sub rsp, 48h

    ; Do some work before hook site
    mov rdi, r8                 ; Put test value into rdi
    lea rax, [rcx + rdx*2]      ; rax = a + 2*b
    mov rbx, 1122334455667788h  ; test non-volatile preservation
    mov r12, 123456789ABCDEF0h
    mov r13, 0A1B2C3D4E5F60718h
    mov r14, 1020304050607080h
    mov r15, 0F0E0D0C0B0A09080h

    ; Mid-function hook site anchor!
mid_hook_site_anchor PROC
    mov r10, rax
    add r10, 100h
    sub r10, 100h
    mov rax, r10
    nop
    nop
    nop
    nop
mid_hook_site_anchor ENDP

    ; Do post-hook work
    add rax, 42h
    add rax, rdi                ; incorporates rdi to verify rdi was preserved

    ; Verify non-volatiles were not corrupted (xor reg, imm64 is not valid in x64, use r11 as temp)
    mov r11, 1122334455667788h
    xor rbx, r11
    add rax, rbx

    mov r11, 123456789ABCDEF0h
    xor r12, r11
    add rax, r12

    mov r11, 0A1B2C3D4E5F60718h
    xor r13, r11
    add rax, r13

    mov r11, 1020304050607080h
    xor r14, r11
    add rax, r14

    mov r11, 0F0E0D0C0B0A09080h
    xor r15, r11
    add rax, r15

    add rsp, 48h
    pop r15
    pop r14
    pop r13
    pop r12
    pop rdi
    pop rsi
    pop rbx
    pop rbp
    ret
target_function_mid_hook ENDP

; Detour stub: exactly matches contact_pair_hook_x64.asm logic
test_mid_function_detour_stub PROC
    pushfq
    push rax
    push rcx
    push rdx
    push r8
    push r9
    push r10
    push r11

    ; Dynamically align stack to 16 bytes, identical to contact_pair_hook_x64.asm
    mov r11, rsp
    and rsp, -16
    sub rsp, 090h
    mov qword ptr [rsp+080h], r11

    movdqu xmmword ptr [rsp+020h], xmm0
    movdqu xmmword ptr [rsp+030h], xmm1
    movdqu xmmword ptr [rsp+040h], xmm2
    movdqu xmmword ptr [rsp+050h], xmm3
    movdqu xmmword ptr [rsp+060h], xmm4
    movdqu xmmword ptr [rsp+070h], xmm5

    mov rcx, rdi                 ; pass rdi as argument to observer
    call test_mid_function_observer

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
    jmp qword ptr [g_test_mid_function_trampoline]
test_mid_function_detour_stub ENDP

END
