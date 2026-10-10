#ifdef __x86_64__
.intel_syntax noprefix
.text
.global bsc_synthetic_transfer
.global bsc_synthetic_patch_site
.global bsc_synthetic_resume
.type bsc_synthetic_transfer,@function
# SysV RDI old state, RSI simulated queue slot base. The central 17 bytes
# are byte-for-byte the WH3 original MS x64 instruction span.
bsc_synthetic_transfer:
 push r14
 push rsi
 sub rsp,40
 mov r14,rsi
 mov rsi,rdi
bsc_synthetic_patch_site:
 .byte 0xff,0x46,0x18
 .byte 0x49,0x8d,0x4e,0x18
 .byte 0x49,0x8b,0x46,0x18
 .byte 0x48,0x8b,0xd6
 .byte 0xff,0x50,0x48
bsc_synthetic_resume:
 add rsp,40
 pop rsi
 pop r14
 ret
.size bsc_synthetic_transfer,.-bsc_synthetic_transfer
.att_syntax prefix
#endif
.section .note.GNU-stack,"",@progbits
