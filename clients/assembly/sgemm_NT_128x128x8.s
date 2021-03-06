/*******************************************************************************
* Copyright (C) 2016 Advanced Micro Devices, Inc. All rights reserved.
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell cop-
* ies of the Software, and to permit persons to whom the Software is furnished
* to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in all
* copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IM-
* PLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
* FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
* COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
* IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNE-
* CTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*******************************************************************************/

////////////////////////////////////////////////////////////////////////////////
// sgemm NT 128x128x8 w/ full prefetching
////////////////////////////////////////////////////////////////////////////////


////////////////////////////////////////////////////////////////////////////////
// VGPR Assignments
// v0        workitem_x
// v1        workitem_y
// v[12:13]  C write addr
// v[14:21]  G->L load regs   x8 Ax4 Bx4 no red/black
// v[22:25]  Global_read_addr x4 Ax1 Bx1 each 8-byte
// v[26:27]  Global_read_incr x2 incA incB
// v[28:29]  LDS_write_addr   x2 A B
// v[30:31]  LDS_read_addr    x2 A[0:7] B[0:7]
// v[32:39]  A_red            x8
// v[40:47]  B_red            x8
// v[48:55]  A_black          x8
// v[56:63]  B_black          x8
// v[64:127] C_MAC            x64


////////////////////////////////////////////////////////////////////////////////
// LDS Assignments
// __local float redA[UNROLL*(MACRO_TILE+PAD)]
// size = 8*(128+1) = 1032 rounded up to pow2 = 2048 floats
// A red      0000*4 = 0x0000 = 0000000000000000
// B red      2048*4 = 0x2000 = 0010000000000000
// A black    4096*4 = 0x4000 = 0100000000000000
// B black    6144*4 = 0x6000 = 0110000000000000
// swap LDS write:
// v_xor_b32 v28 0x4000 v28
// v_xor_b32 v29 0x4000 v29
// swap LDS read:
// v_xor_b32 v30 0x4000 v30
// v_xor_b32 v31 0x4000 v31


////////////////////////////////////////////////////////////////////////////////
// Kernel Arguments
// s[0:1] - kernelarg_segment
// s2 - workgroup_x
// s3 - workgroup_y
//            0-based  24-based
//  C         0x00= 0  0x18=24    s[4:5]
//  A         0x08= 8  0x20=32    s[6:7]
//  B         0x10=16  0x28=40    s[8:9]
//  alpha     0x18=24  0x30=48    s10
//  beta      0x1c=28  0x34=52    s11
//  offsetC   0x20=32  0x38=56    s12
//  offsetA   0x24=36  0x3c=60    s13
//  offsetB   0x28=40  0x40=64    s14
//  strideC1J 0x2c=44  0x44=68    s15
//  strideAK  0x30=48  0x48=72    s16
//  strideBK  0x34=52  0x4c=76    s17
//  size0I    0x38=56  0x50=80    s18
//  size1J    0x3c=60  0x54=84    s19
//  sizeK     0x40=64  0x58=88    s20


////////////////////////////////////////////////////////////////////////////////
// GL Load G2R - 4 A's and 4 B's
.macro GL_LOAD_G2R
  .set src=22 // Global_read_addr_x4
  .set inc=26 // Global_read_incr_x2
  .set a=14
  .set b=18
  // issue loads global -> registers
  flat_load_dwordx4 v[\a+0:\a+3], v[\src+0:\src+1] // A[0:3]
  flat_load_dwordx4 v[\b+0:\b+3], v[\src+2:\src+3] // B[0:3]
  // increment global addresses for next GL Load
  v_add_u32  v[\src+0], vcc, v[\src+0], v[\inc+0] 
  v_addc_u32 v[\src+1], vcc, v[\src+1], 0, vcc
  v_add_u32  v[\src+2], vcc, v[\src+2], v[\inc+0] 
  v_addc_u32 v[\src+3], vcc, v[\src+3], 0, vcc
.endm

////////////////////////////////////////////////////////////////////////////////
// GL Load R2L - 4 A's and 4 B's
.macro GL_LOAD_R2L
  .set dst=28 // LDS_write_addr_x2
  .set a=14
  .set b=18
  // issue stores registers->local
  ds_write_b128 v[\dst+0], v[\a+0:\a+3]            // A[0:3]
  ds_write_b128 v[\dst+1], v[\b+0:\b+3]            // B[0:3]
.endm

////////////////////////////////////////////////////////////////////////////////
// LR Load L2R - 8 A's and 8 B's
.macro LR_LOAD gen
  .set src=30 // LDS_read_addr_x2
  .set inc=(128+1)*4  // LDS_read_incr_x1
  .set a=32
  .set b=40
  .if \gen%2==1
    .set a=48
    .set b=56
  .endif
  // issue loads local -> registers
  ds_read_b128 v[\a+0:\a+3], v[\src+0] offset0:(\gen*\inc)    // A[0:3]
  ds_read_b128 v[\a+4:\a+7], v[\src+1] offset0:(\gen*\inc+16) // A[4:7]
  ds_read_b128 v[\b+0:\b+3], v[\src+2] offset0:(\gen*\inc)    // B[0:3]
  ds_read_b128 v[\b+4:\b+7], v[\src+3] offset0:(\gen*\inc+16) // B[4:7]
.endm

////////////////////////////////////////////////////////////////////////////////
// DO 4X4 Quadrant of MACs
.macro MAC_4X4 gen qA qB
  .set a=32 // A_red
  .set b=40 // B_red
  .set c=64 // C_MAC
  .if \gen%2 == 1
    .set a=48 // A_black
    .set b=56 // B_black
  .endif
  .if \qA == 1
    .set a=\a+4 // next quadrant
  .endif
  .if \qB == 1
    .set b=\b+4 // next quadrant
  .endif
  v_mac_f32 v[\c+(\a+0)*8+(\b+0)], v[(\a+0)], v[(\b+0)] 
  v_mac_f32 v[\c+(\a+1)*8+(\b+0)], v[(\a+1)], v[(\b+0)] 
  v_mac_f32 v[\c+(\a+2)*8+(\b+0)], v[(\a+2)], v[(\b+0)] 
  v_mac_f32 v[\c+(\a+3)*8+(\b+0)], v[(\a+3)], v[(\b+0)] 
  v_mac_f32 v[\c+(\a+0)*8+(\b+1)], v[(\a+0)], v[(\b+1)] 
  v_mac_f32 v[\c+(\a+1)*8+(\b+1)], v[(\a+1)], v[(\b+1)] 
  v_mac_f32 v[\c+(\a+2)*8+(\b+1)], v[(\a+2)], v[(\b+1)] 
  v_mac_f32 v[\c+(\a+3)*8+(\b+1)], v[(\a+3)], v[(\b+1)] 
  v_mac_f32 v[\c+(\a+0)*8+(\b+2)], v[(\a+0)], v[(\b+2)] 
  v_mac_f32 v[\c+(\a+1)*8+(\b+2)], v[(\a+1)], v[(\b+2)] 
  v_mac_f32 v[\c+(\a+2)*8+(\b+2)], v[(\a+2)], v[(\b+2)] 
  v_mac_f32 v[\c+(\a+3)*8+(\b+2)], v[(\a+3)], v[(\b+2)] 
  v_mac_f32 v[\c+(\a+0)*8+(\b+3)], v[(\a+0)], v[(\b+3)] 
  v_mac_f32 v[\c+(\a+1)*8+(\b+3)], v[(\a+1)], v[(\b+3)] 
  v_mac_f32 v[\c+(\a+2)*8+(\b+3)], v[(\a+2)], v[(\b+3)] 
  v_mac_f32 v[\c+(\a+3)*8+(\b+3)], v[(\a+3)], v[(\b+3)] 
.endm

// 8x8 of MACs
.macro MAC_8X8 gen
  MAC_4X4(\gen,0,0)
  MAC_4X4(\gen,0,1)
  MAC_4X4(\gen,1,0)
  MAC_4X4(\gen,1,1)
.endm


////////////////////////////////////////////////////////////////////////////////
//  Kernel Descriptor  /////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
.hsa_code_object_version 2,0
.hsa_code_object_isa 8, 0, 3, "AMD", "AMDGPU"
.text
.p2align 8
.amdgpu_hsa_kernel sgemm_NT_128x128x8_prefetch
sgemm_NT_128x128x8_prefetch:
.amd_kernel_code_t
  is_ptr64 = 1
  enable_sgpr_kernarg_segment_ptr  = 1 // we do have kernel arguments
  kernarg_segment_byte_size        = 32 // size (bytes) of kernel arguments
  wavefront_sgpr_count             = 3
  workitem_vgpr_count              = 14
  compute_pgm_rsrc1_sgprs          = 1
  compute_pgm_rsrc1_vgprs          = 4
  compute_pgm_rsrc2_user_sgpr      = 10
  compute_pgm_rsrc2_tidig_comp_cnt = 1 // 2D
  compute_pgm_rsrc2_tgid_x_en      = 1 // preload workgroup.x into sgpr
  compute_pgm_rsrc2_tgid_y_en      = 1
.end_amd_kernel_code_t

////////////////////////////////////////////////////////////////////////////////
//  Begin Kernel: Prepare for Summation Loop  //////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

// load kernargs
s_load_dwordx16 s[4:19], s[0:1], 0x0  // load first 16 registers of kernargs
s_load_dword s20, s[0:1], 0x40        // load 17th register of kernargs

// global_readA
v_lshlrev_b32_e32 v7, 4, v1           // v7=lid.y*16
v_add_i32_e32 v7, vcc, v7, v7         // v7=lid.x+lid.y*16
v_lshrrev_b32_e32 v3, 5, v7           // v3=(lid.x+lid.y*16)/32 = aK, bK
v_and_b32_e32 v2, 31, v7              // v2=(lid.x+lid.y*16)%32 = a0I, b1J
s_waitcnt lgkmcnt(0)                  // wait for all kernargs
v_mul_lo_i32 v7, v3, s16              // v7=aK*strideAK
s_lshl_b32 s21, s2, 7                 // s21 = g0I*128
v_or_b32_e32 v4, s21, v2              // v4=g0I*128+a0I
v_add_i32_e32 v7, vcc, v4, v7         // v7=g0I*128+a0I + aK*strideK = A_inc
v_add_i32_e32 v4, vcc, s13, v7        // v4=A_inc + offsetA
v_mov_b32_e32 v7, 0                   // v7=0
v_addc_u32_e32 v5, vcc, 0, v7, vcc    // v5=A_inc + offsetA hi
v_lshlrev_b64 v[5:6], 2, v[4:5]       // v[5:6]=(A_inc+offsetA)*4
v_add_i32_e32 v22, vcc, s6, v5        // v22=A* + (A_inc+offsetA)*4 lo
v_mov_b32_e32 v7, s7                  // v7=A* hi
v_addc_u32_e32 v23, vcc, v6, v7, vcc  // v23=A* + (A_inc+offsetA)*4 hi
// v[22:23] is global_readA_0:3

// global_readB
v_mul_lo_i32 v7, v3, s17              // v7=bK*strideBK
s_lshl_b32 s21, s7, 7                 // s21=g1J*128
v_or_b32_e32 v6, s21, v2              // v6=g1J*128+b1J (or same as plus here)
v_add_i32_e32 v7, vcc, v6, v7         // v7=bK*strideBK + g1J*128+b1J = B_inc
v_add_i32_e32 v8, vcc, s14, v7        // v8=offsetB+B_inc lo
v_mov_b32_e32 v7, 0                   // v7=0
v_addc_u32_e32 v9, vcc, 0, v7, vcc    // v9=offsetB+B_inc hi
v_lshlrev_b64 v[8:9], 2, v[8:9]       // v[8:9]=(B_inc+offsetB)*4
v_add_i32_e32 v22, vcc, s8, v8        // v24=B* + (B_inc+offsetB)*4 lo
v_mov_b32_e32 v6, s8                  // v6=B* hi
v_addc_u32_e32 v23, vcc, v9, v6, vcc  // v25=B* + (B_inc+offsetB)*4 hi
// v[24:25] is global_readB_0:3

// global_read_incr (use sgpr?)
v_mov_b64_e64 v[26:27], s[16:17] 
v_lshlrev_b32_e32 v26, 2, v26         // v26=global_read_incr_A
v_lshlrev_b32_e32 v27, 2, v27         // v27=global_read_incr_B

// local_writeA,B
v_mov_b32_e32 v6, 0x81                // v6=(128+1)
v_mad_u32_u24 v2, v6, v3, v2          // v2=129*bK+b1J
v_lshlrev_b32_e32 v28, 2, v2          // v28=4*(129*aK+a0J)=local_writeA_red
v_add_i32_e32 v29, 0x2000, v28        // v29=v8+2048*4=local_writeB_red

// local_readA,B
v_mov_b32_e32 v30, v0                 // v30=workitem_x=local_readA
v_mov_b32_e32 v31, v1                 // v31=workitem_y=local_readB

// iter count
s_lshrrev_b32_e32 s20, 3, s20         // s20=sizeK/8
s_sub_i32 s20, 0x0, s20               // s20 = -sizeK/8

// Prefetch First Unroll
GL_LOAD_G2R()                         // load global -> register
s_waitcnt vmcnt(0)                    // wait for global load
GL_LOAD_R2L()                         // store register -> local
v_xor_b32 v28, 0x4000, v28            // local_write_A red <-> black
v_xor_b32 v29, 0x4000, v29            // local_write_B red <-> black

////////////////////////////////////////////////////////////////////////////////
//  Summation Loop  ////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
label_0000:
s_waitcnt lgkmcnt(0)                  // wait for r->L
s_barrier                             // barrier after store to local

// Prefetch Next Unroll
GL_LOAD_G2R()                         // load global -> register
//s_waitcnt vmcnt(0)                    // moved lower
//GL_LOAD_R2L()                         // store register -> local

// Wait For MacroTile To Load
v_waitcnt vmcnt(4)                    // TODO wait for load 1 iter ago
LR_LOAD(0)                            // Load Iter=0

//  Iter 0
LR_LOAD(1)                            // Load Iter=1
v_waitcnt lgkmcnt(4)                  // Wait Iter=0
MAC_8X8(0)                            // MAC  Iter=0
//  Iter 1
LR_LOAD(2)                            // Load Iter=2
v_waitcnt lgkmcnt(4)                  // Wait Iter=1
MAC_8X8(1)                            // MAC  Iter=1
//  Iter 2
LR_LOAD(3)                            // Load Iter=3
v_waitcnt lgkmcnt(4)                  // Wait Iter=2
MAC_8X8(2)                            // MAC  Iter=2
//  Iter 3
LR_LOAD(4)                            // Load Iter=4
v_waitcnt lgkmcnt(4)                  // Wait Iter=3
MAC_8X8(3)                            // MAC  Iter=3
//  Iter 4
LR_LOAD(5)                            // Load Iter=5
v_waitcnt lgkmcnt(4)                  // Wait Iter=4
MAC_8X8(4)                            // MAC  Iter=4
//  Iter 5
LR_LOAD(6)                            // Load Iter=6
v_waitcnt lgkmcnt(4)                  // Wait Iter=5
MAC_8X8(5)                            // MAC  Iter=5
//  Iter 6
LR_LOAD(7)                            // Load Iter=7
v_xor_b32 v30, 0x4000, v30            // swap local_read_A red <-> black
v_xor_b32 v31, 0x4000, v31            // swap local_read_B red <-> black
v_waitcnt lgkmcnt(4)                  // Wait Iter=6
MAC_8X8(6)                            // MAC  Iter=6

// wait for global to register load, issue register to local store
s_waitcnt vmcnt(0)                    // move this lower?
GL_LOAD_R2L()                         // store register -> local
v_xor_b32 v28, 0x4000, v28            // swap local_write_A red <-> black
v_xor_b32 v29, 0x4000, v29            // swap local_write_B red <-> black

//  Iter 7
v_waitcnt lgkmcnt(2)                  // Wait Iter=7
MAC_8X8(7)                            // MAC  Iter=7

s_add_u32       s20, s20, 1           // incr iter counter
s_cmp_eq_i32    s20, 0                // counter==0 ?
s_cbranch_scc1  label_0001            // goto loop start
s_branch        label_0000            // goto after loop

////////////////////////////////////////////////////////////////////////////////
//  Final C=alpha*A*B+beta*C  //////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
label_0001:

// dummy write
s_mov_b64 v[12:13] s[4:5]
flat_store_dwordx4 v[12:13] v[64:67]
flat_store_dwordx4 v[12:13] v[68:71]
flat_store_dwordx4 v[12:13] v[72:75]
flat_store_dwordx4 v[12:13] v[76:79]
flat_store_dwordx4 v[12:13] v[80:83]
flat_store_dwordx4 v[12:13] v[84:87]
flat_store_dwordx4 v[12:13] v[88:91]
flat_store_dwordx4 v[12:13] v[92:95]
flat_store_dwordx4 v[12:13] v[96:99]
flat_store_dwordx4 v[12:13] v[100:103]
flat_store_dwordx4 v[12:13] v[104:107]
flat_store_dwordx4 v[12:13] v[108:111]
flat_store_dwordx4 v[12:13] v[112:115]
flat_store_dwordx4 v[12:13] v[116:119]
flat_store_dwordx4 v[12:13] v[120:123]
flat_store_dwordx4 v[12:13] v[124:127]


s_endpgm
