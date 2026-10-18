# BSC R43 user-original EXE SHA256 9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496
# All addresses RVA; extracted with GNU objdump; context excerpts, not runtime traces.

# typed member constructor/vtable selected [03052D1E..03052D38) from 03052BA8..0305362D
03052D20 lea    rax,[rip+0x8bfc29]        # 0x3912950
03052D27 mov    QWORD PTR [rbx+0x260],rdi
03052D2E mov    r9d,0x3f800000
03052D34 mov    QWORD PTR [rbx],rax
03052D37 mov    r8d,0x269ec3

# embedded pending record constructor selected [03051D98..03051DF1) from 03051D98..03051DF1
03051D98 sub    rsp,0x28
03051D9C and    WORD PTR [rcx],0x0
03051DA0 lea    rdx,[rip+0x1021411]        # 0x40731b8
03051DA7 movss  xmm0,DWORD PTR [rip+0x1021409]        # 0x40731b8
03051DAF mov    r11,rcx
03051DB2 movss  DWORD PTR [rcx+0x4],xmm0
03051DB7 xor    r9d,r9d
03051DBA movss  xmm1,DWORD PTR [rip+0x10213fa]        # 0x40731bc
03051DC2 movss  DWORD PTR [rcx+0x8],xmm1
03051DC7 movss  xmm0,DWORD PTR [rip+0x10213f1]        # 0x40731c0
03051DCF movss  DWORD PTR [rcx+0xc],xmm0
03051DD4 add    rcx,0x10
03051DD8 movzx  r8d,WORD PTR [rip+0x6cdc6c]        # 0x371fa4c
03051DE0 call   0x2d9f998
03051DE5 mov    rax,r11
03051DE8 mov    BYTE PTR [r11+0x28],r9b
03051DEC add    rsp,0x28
03051DF0 ret

# member embeds pending record selected [0305304C..0305312D) from 03052BA8..0305362D
0305304C mov    QWORD PTR [rbx+0x850],r12
03053053 movss  xmm0,DWORD PTR [rip+0x10201fd]        # 0x4073258
0305305B movss  DWORD PTR [rbx+0x858],xmm0
03053063 lea    r14d,[r15-0x2]
03053067 movss  xmm1,DWORD PTR [rip+0x10201ed]        # 0x407325c
0305306F lea    rcx,[rbx+0x8d8]
03053076 movss  DWORD PTR [rbx+0x85c],xmm1
0305307E mov    r15d,0x3f800000
03053084 movss  xmm0,DWORD PTR [rip+0x10201d4]        # 0x4073260
0305308C movss  DWORD PTR [rbx+0x860],xmm0
03053094 mov    QWORD PTR [rbx+0x868],r12
0305309B mov    QWORD PTR [rbx+0x870],r12
030530A2 mov    WORD PTR [rbx+0x878],r12w
030530AA mov    QWORD PTR [rbx+0x87c],0x81
030530B5 mov    DWORD PTR [rbx+0x884],r12d
030530BC mov    WORD PTR [rbx+0x888],r12w
030530C4 mov    BYTE PTR [rbx+0x88a],r14b
030530CB mov    QWORD PTR [rbx+0x890],r12
030530D2 mov    QWORD PTR [rbx+0x898],r12
030530D9 mov    DWORD PTR [rbx+0x8a0],r15d
030530E0 mov    WORD PTR [rbx+0x8a4],r14w
030530E8 mov    DWORD PTR [rbx+0x8a8],r12d
030530EF mov    WORD PTR [rbx+0x8ac],r14w
030530F7 mov    DWORD PTR [rbx+0x8b0],0x2
03053101 mov    WORD PTR [rbx+0x8b4],r12w
03053109 mov    QWORD PTR [rbx+0x8b8],r12
03053110 mov    QWORD PTR [rbx+0x8c0],r12
03053117 mov    DWORD PTR [rbx+0x8c8],r12d
0305311E mov    DWORD PTR [rbx+0x8d0],0x3c23d70a
03053128 call   0x3051d98

# member tick pending gate + post cleanup selected [03086F48..03087060) from 03086F04..0308774C
03086F48 xor    r14d,r14d
03086F4B test   al,al
03086F4D jne    0x3086f5a
03086F4F mov    eax,0xfffeffff
03086F54 and    DWORD PTR [rdi+0x6c],eax
03086F57 and    DWORD PTR [rdi+0x70],eax
03086F5A mov    dl,BYTE PTR [rdi+0x108]
03086F60 mov    al,BYTE PTR [rdi+0xb12]
03086F66 and    dl,0x10
03086F69 je     0x3086f70
03086F6B mov    cl,r14b
03086F6E jmp    0x3086f75
03086F70 mov    cl,al
03086F72 and    cl,0x80
03086F75 and    al,0x7f
03086F77 or     al,cl
03086F79 mov    BYTE PTR [rdi+0xb12],al
03086F7F test   dl,dl
03086F81 jne    0x3086fcc
03086F83 cmp    DWORD PTR [rdi+0x26c],0x7c
03086F8A jne    0x3086fcc
03086F8C mov    rcx,rdi
03086F8F call   0x306bae0
03086F94 test   al,al
03086F96 jne    0x3086fcc
03086F98 mov    rcx,rdi
03086F9B call   0x3090a80
03086FA0 mov    rcx,rdi
03086FA3 call   0x308e774
03086FA8 lea    rcx,[rdi+0xaf0]
03086FAF mov    rdx,rdi
03086FB2 call   0x32654d0
03086FB7 mov    rcx,rdi
03086FBA call   0x308e2a0
03086FBF mov    rcx,rdi
03086FC2 call   0x3088304
03086FC7 jmp    0x308771b
03086FCC mov    r15d,0x1
03086FD2 cmp    BYTE PTR [rdi+0x8d8],r14b
03086FD9 je     0x308706f
03086FDF mov    al,BYTE PTR [rdi+0x900]
03086FE5 lea    r8,[rdi+0x8dc]
03086FEC mov    BYTE PTR [rsp+0x38],r14b
03086FF1 lea    rdx,[rdi+0x8e8]
03086FF8 mov    BYTE PTR [rsp+0x30],r14b
03086FFD mov    r9b,r15b
03087000 mov    QWORD PTR [rsp+0x28],r14
03087005 mov    rcx,rdi
03087008 mov    BYTE PTR [rsp+0x20],al
0308700C mov    BYTE PTR [rdi+0x8d8],r14b
03087013 call   0x3065db8
03087018 mov    WORD PTR [rdi+0x8d8],r14w
03087020 lea    rdx,[rip+0xfec191]        # 0x40731b8
03087027 movsd  xmm0,QWORD PTR [rip+0xfec189]        # 0x40731b8
0308702F lea    rcx,[rsp+0x40]
03087034 movsd  QWORD PTR [rdi+0x8dc],xmm0
0308703C xor    r9d,r9d
0308703F mov    eax,DWORD PTR [rip+0xfec17b]        # 0x40731c0
03087045 mov    DWORD PTR [rdi+0x8e4],eax
0308704B movzx  r8d,WORD PTR [rip+0x6989f9]        # 0x371fa4c
03087053 call   0x2d9f998
03087058 movups xmm0,XMMWORD PTR [rax]
0308705B movups XMMWORD PTR [rdi+0x8e8],xmm0

# typed pending→goal/velocity copier selected [03065E82..03065EBC) from 03065DB8..03065F43
03065E82 mov    rcx,rbx
03065E85 call   0x3083edc
03065E8A movups xmm0,XMMWORD PTR [rdi]
03065E8D mov    r9b,BYTE PTR [rsp+0x80]
03065E95 mov    r8b,sil
03065E98 mov    rdx,rbp
03065E9B mov    rcx,rbx
03065E9E movups XMMWORD PTR [rbx+0x1e0],xmm0
03065EA5 movsd  xmm1,QWORD PTR [rdi+0x10]
03065EAA movsd  QWORD PTR [rbx+0x1f0],xmm1
03065EB2 call   0x3154974
03065EB7 mov    rcx,rbx
03065EBA call   0x3085f78

# actual vector-to-delta install selected [03154974..03154A96) from 03154974..03154A96
03154974 mov    QWORD PTR [rsp+0x8],rbx
03154979 mov    QWORD PTR [rsp+0x10],rsi
0315497E push   rdi
0315497F sub    rsp,0x30
03154983 mov    bl,r9b
03154986 mov    r11b,r8b
03154989 mov    r10,rdx
0315498C mov    rdi,rcx
0315498F call   0x3169594
03154994 movsd  xmm0,QWORD PTR [r10]
03154999 xorps  xmm2,xmm2
0315499C mov    dl,BYTE PTR [rcx+0x108]
031549A2 xor    esi,esi
031549A4 movsd  QWORD PTR [rcx+0xe0],xmm0
031549AC or     dl,0x2
031549AF mov    eax,DWORD PTR [r10+0x8]
031549B3 movss  xmm0,DWORD PTR [rip+0x7cdf0d]        # 0x39228c8
031549BB mov    DWORD PTR [rcx+0xe8],eax
031549C1 mov    eax,DWORD PTR [rip+0xbb98cd]        # 0x3d0e294
031549C7 mov    DWORD PTR [rcx+0xec],esi
031549CD shl    r11b,0x6
031549D1 cvtsi2ss xmm2,rax
031549D6 movaps xmm3,xmm2
031549D9 movaps xmm1,xmm2
031549DC mulss  xmm3,DWORD PTR [r10]
031549E1 mulss  xmm1,DWORD PTR [r10+0x4]
031549E7 mulss  xmm2,DWORD PTR [r10+0x8]
031549ED mov    WORD PTR [rcx+0x148],si
031549F4 mulss  xmm1,xmm0
031549F8 mulss  xmm2,xmm0
031549FC mulss  xmm3,xmm0
03154A00 movss  DWORD PTR [rsp+0x28],xmm2
03154A06 mov    eax,DWORD PTR [rsp+0x28]
03154A0A movaps xmm0,xmm3
03154A0D unpcklps xmm0,xmm1
03154A10 movsd  QWORD PTR [rcx+0x13c],xmm0
03154A18 mov    DWORD PTR [rcx+0x144],eax
03154A1E movss  xmm0,DWORD PTR [rip+0xf1e852]        # 0x4073278
03154A26 movss  DWORD PTR [rcx+0x14c],xmm0
03154A2E movss  xmm1,DWORD PTR [rip+0xf1e846]        # 0x407327c
03154A36 and    BYTE PTR [rcx+0x155],0xbf
03154A3D or     BYTE PTR [rcx+0x155],r11b
03154A44 movss  DWORD PTR [rcx+0x150],xmm1
03154A4C mov    BYTE PTR [rcx+0x108],dl
03154A52 test   bl,bl
03154A54 je     0x3154a6d
03154A56 mov    rax,QWORD PTR [rcx+0x58]
03154A5A mov    rcx,QWORD PTR [rax+0x440]
03154A61 mov    eax,DWORD PTR [rcx+0x98]
03154A67 mov    DWORD PTR [rdi+0x100],eax
03154A6D test   dl,0x4
03154A70 jne    0x3154a7e
03154A72 mov    rax,QWORD PTR [rdi]
03154A75 mov    rcx,rdi
03154A78 call   QWORD PTR [rax+0x128]
03154A7E mov    rbx,QWORD PTR [rsp+0x40]
03154A83 mov    QWORD PTR [rdi+0x20],rsi
03154A87 mov    QWORD PTR [rdi+0x30],rsi
03154A8B mov    rsi,QWORD PTR [rsp+0x48]
03154A90 add    rsp,0x30
03154A94 pop    rdi
03154A95 ret

# leaf helper preserves volatile argument registers selected [03169594..03169629) from 03169594..03169629
03169594 mov    rdx,QWORD PTR [rcx+0x20]
03169598 xor    r9d,r9d
0316959B test   rdx,rdx
0316959E je     0x31695dd
031695A0 mov    r8,QWORD PTR [rcx+0x10]
031695A4 test   r8,r8
031695A7 je     0x31695b1
031695A9 mov    rax,QWORD PTR [rcx+0x8]
031695AD mov    QWORD PTR [r8+0x8],rax
031695B1 mov    r8,QWORD PTR [rcx+0x8]
031695B5 test   r8,r8
031695B8 je     0x31695c2
031695BA mov    rax,QWORD PTR [rcx+0x10]
031695BE mov    QWORD PTR [r8+0x10],rax
031695C2 cmp    QWORD PTR [rdx+0x58],rcx
031695C6 jne    0x31695d0
031695C8 mov    rax,QWORD PTR [rcx+0x8]
031695CC mov    QWORD PTR [rdx+0x58],rax
031695D0 mov    QWORD PTR [rcx+0x10],r9
031695D4 mov    QWORD PTR [rcx+0x8],r9
031695D8 dec    DWORD PTR [rdx+0x60]
031695DB jmp    0x3169621
031695DD mov    rdx,QWORD PTR [rcx+0x30]
031695E1 test   rdx,rdx
031695E4 je     0x3169621
031695E6 mov    r8,QWORD PTR [rcx+0x10]
031695EA test   r8,r8
031695ED je     0x31695f7
031695EF mov    rax,QWORD PTR [rcx+0x8]
031695F3 mov    QWORD PTR [r8+0x8],rax
031695F7 mov    r8,QWORD PTR [rcx+0x8]
031695FB test   r8,r8
031695FE je     0x3169608
03169600 mov    rax,QWORD PTR [rcx+0x10]
03169604 mov    QWORD PTR [r8+0x10],rax
03169608 cmp    QWORD PTR [rdx+0x40],rcx
0316960C jne    0x3169616
0316960E mov    rax,QWORD PTR [rcx+0x8]
03169612 mov    QWORD PTR [rdx+0x40],rax
03169616 mov    QWORD PTR [rcx+0x10],r9
0316961A mov    QWORD PTR [rcx+0x8],r9
0316961E dec    DWORD PTR [rdx+0x48]
03169621 mov    QWORD PTR [rcx+0xf8],r9
03169628 ret

# alternate target setter selected [03071CA1..03071CEA) from 03071C84..03071CEA
03071CA1 mov    rbp,rcx
03071CA4 call   0x3083edc
03071CA9 movups xmm0,XMMWORD PTR [rbx]
03071CAC mov    r8b,dil
03071CAF mov    rdx,rsi
03071CB2 mov    rcx,rbp
03071CB5 movups XMMWORD PTR [rbp+0x1e0],xmm0
03071CBC movsd  xmm1,QWORD PTR [rbx+0x10]
03071CC1 movsd  QWORD PTR [rbp+0x1f0],xmm1
03071CC9 call   0x315fb24
03071CCE mov    rcx,rbp
03071CD1 mov    rbx,QWORD PTR [rsp+0x30]
03071CD6 mov    rbp,QWORD PTR [rsp+0x38]
03071CDB mov    rsi,QWORD PTR [rsp+0x40]
03071CE0 add    rsp,0x20
03071CE4 pop    rdi
03071CE5 jmp    0x3085f78

# alternate delta reset selected [0315FB3C..0315FC21) from 0315FB24..0315FC3B
0315FB3C call   0x3169594
0315FB41 test   r10b,r10b
0315FB44 jne    0x315fb5b
0315FB46 movsd  xmm0,QWORD PTR [rsi]
0315FB4A movsd  QWORD PTR [rcx+0xe0],xmm0
0315FB52 mov    eax,DWORD PTR [rsi+0x8]
0315FB55 mov    DWORD PTR [rcx+0xe8],eax
0315FB5B movsd  xmm0,QWORD PTR [rip+0xf13705]        # 0x4073268
0315FB63 lea    rdx,[rsp+0x40]
0315FB68 movsd  QWORD PTR [rcx+0x13c],xmm0
0315FB70 mov    eax,DWORD PTR [rip+0xf136fa]        # 0x4073270
0315FB76 mov    DWORD PTR [rcx+0x144],eax
0315FB7C mov    rax,QWORD PTR [rcx]
0315FB7F call   QWORD PTR [rax+0xc8]
0315FB85 movss  xmm1,DWORD PTR [rsi+0x8]
0315FB8A mov    rbx,rax
0315FB8D movss  xmm0,DWORD PTR [rsi]
0315FB91 call   0x1183a8c
0315FB96 mulss  xmm0,DWORD PTR [rip+0x7c26c2]        # 0x3922260
0315FB9E call   0x4eda50
0315FBA3 sub    ax,WORD PTR [rbx]
0315FBA6 mov    ecx,0x8000
0315FBAB mov    WORD PTR [rdi+0x148],ax
0315FBB2 movss  xmm0,DWORD PTR [rip+0xf136be]        # 0x4073278
0315FBBA movss  DWORD PTR [rdi+0x14c],xmm0
0315FBC2 movss  xmm1,DWORD PTR [rip+0xf136b2]        # 0x407327c
0315FBCA movss  DWORD PTR [rdi+0x150],xmm1
0315FBD2 cmp    ax,cx
0315FBD5 je     0x315fbda
0315FBD7 movsx  ecx,ax
0315FBDA test   BYTE PTR [rdi+0x108],0x4
0315FBE1 xorps  xmm0,xmm0
0315FBE4 mov    eax,DWORD PTR [rip+0xbae6aa]        # 0x3d0e294
0315FBEA movss  xmm2,DWORD PTR [rip+0x990896]        # 0x3af0488
0315FBF2 movd   xmm1,ecx
0315FBF6 cvtdq2ps xmm1,xmm1
0315FBF9 cvtsi2ss xmm0,rax
0315FBFE divss  xmm2,xmm0
0315FC02 mulss  xmm2,xmm1
0315FC06 movss  DWORD PTR [rdi+0xec],xmm2
0315FC0E jne    0x315fc1c
0315FC10 mov    rax,QWORD PTR [rdi]
0315FC13 mov    rcx,rdi
0315FC16 call   QWORD PTR [rax+0x128]
0315FC1C bts    DWORD PTR [rdi+0x6c],0x8

# integrator earliest delta gates selected [03147060..031471D4) from 03146FF0..03148523
03147060 movss  xmm0,DWORD PTR [rcx+0x150]
03147068 movss  xmm1,DWORD PTR [rcx+0x14c]
03147070 mulss  xmm1,xmm1
03147074 mulss  xmm0,xmm0
03147078 movaps XMMWORD PTR [rsp+0x70],xmm15
0314707E addss  xmm1,xmm0
03147082 comiss xmm1,xmm11
03147086 jbe    0x31471a9
0314708C movzx  eax,WORD PTR [rcx+0x148]
03147093 test   ax,ax
03147096 jns    0x314709b
03147098 neg    ax
0314709B cmp    ax,r14w
0314709F je     0x31470aa
031470A1 test   ax,ax
031470A4 jle    0x31471a9
031470AA mov    rax,QWORD PTR [rcx]
031470AD lea    rdx,[rbp+0x67]
031470B1 call   QWORD PTR [rax+0xc8]
031470B7 movzx  ecx,WORD PTR [rax]
031470BA movzx  eax,WORD PTR [rbx+0x148]
031470C1 add    ax,cx
031470C4 movsx  ecx,ax
031470C7 cmp    ax,r14w
031470CB jne    0x31470d0
031470CD mov    ecx,r14d
031470D0 movss  xmm6,DWORD PTR [rbx+0x150]
031470D8 movd   xmm0,ecx
031470DC cvtdq2ps xmm0,xmm0
031470DF mulss  xmm0,xmm10
031470E4 call   0x1120900
031470E9 movss  xmm1,DWORD PTR [rbx+0x14c]
031470F1 lea    rdx,[rbp+0x6f]
031470F5 mov    rax,QWORD PTR [rbx]
031470F8 movaps xmm7,xmm0
031470FB shufps xmm7,xmm0,0x1
031470FF movaps xmm8,xmm1
03147103 movaps xmm2,xmm0
03147106 mulss  xmm8,xmm7
0314710B mov    rcx,rbx
0314710E mulss  xmm0,xmm6
03147112 mulss  xmm1,xmm2
03147116 mulss  xmm7,xmm6
0314711A addss  xmm8,xmm0
0314711F subss  xmm7,xmm1
03147123 call   QWORD PTR [rax+0xc8]
03147129 cmp    WORD PTR [rax],r14w
0314712D je     0x3147134
0314712F movsx  eax,WORD PTR [rax]
03147132 jmp    0x3147137
03147134 mov    eax,r14d
03147137 movss  xmm6,DWORD PTR [rbx+0x150]
0314713F xorps  xmm1,xmm1
03147142 cvtsi2ss xmm1,eax
03147146 mulss  xmm1,xmm10
0314714B movaps xmm0,xmm1
0314714E call   0x1120900
03147153 movss  xmm2,DWORD PTR [rbx+0x14c]
0314715B movaps xmm4,xmm0
0314715E shufps xmm4,xmm0,0x1
03147162 movaps xmm1,xmm2
03147165 mulss  xmm1,xmm4
03147169 movaps xmm3,xmm0
0314716C mulss  xmm4,xmm6
03147170 mulss  xmm0,xmm6
03147174 mulss  xmm2,xmm3
03147178 addss  xmm1,xmm0
0314717C subss  xmm4,xmm2
03147180 subss  xmm1,xmm8
03147185 subss  xmm4,xmm7
03147189 addss  xmm1,DWORD PTR [rbx+0x13c]
03147191 addss  xmm4,DWORD PTR [rbx+0x144]
03147199 movss  DWORD PTR [rbx+0x13c],xmm1
031471A1 movss  DWORD PTR [rbx+0x144],xmm4
031471A9 mov    dl,BYTE PTR [rbx+0x108]
031471AF mov    cl,BYTE PTR [rbx+0x155]
031471B5 test   dl,0x2
031471B8 jne    0x314738f
031471BE mov    sil,0xfd
031471C1 test   cl,0x4
031471C4 je     0x3147306
031471CA mov    rax,QWORD PTR [rbx+0xf8]
031471D1 test   rax,rax

# integrator reset selected [031472BB..0314730F) from 03146FF0..03148523
031472BB movsd  xmm0,QWORD PTR [rip+0xf2bfa5]        # 0x4073268
031472C3 movsd  QWORD PTR [rbx+0x13c],xmm0
031472CB mov    eax,DWORD PTR [rip+0xf2bf9f]        # 0x4073270
031472D1 mov    DWORD PTR [rbx+0x144],eax
031472D7 mov    WORD PTR [rbx+0x148],r15w
031472DF movss  xmm0,DWORD PTR [rip+0xf2bf91]        # 0x4073278
031472E7 movss  DWORD PTR [rbx+0x14c],xmm0
031472EF movss  xmm1,DWORD PTR [rip+0xf2bf85]        # 0x407327c
031472F7 and    BYTE PTR [rbx+0x154],sil
031472FE movss  DWORD PTR [rbx+0x150],xmm1
03147306 movss  xmm0,DWORD PTR [rip+0xf2bf6a]        # 0x4073278
0314730E movss  DWORD PTR [rbx+0x118],xmm0
