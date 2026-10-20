// tb_post.v -- self-checking testbench for post (ARCHITECTURE.md, section `post`).
//
// Authored by Claude for projects/demo/ (see README.md: Article I override).
//
// Reference: h = min((max(acc,0) * QM + 2^(QSHIFT-1)) >> QSHIFT, QMAX), computed here
// independently in 64-bit integer arithmetic from the same quant_params.vh.
//
// Timing is checked every cycle against a 3-deep model of start: done must equal
// "start was high three cycles ago", h must match on done and must hold otherwise.
// That catches a wrong latency, a stretched or missing done, and a done with no start.
//
// Stimulus: one isolated start with an explicit latency count; directed values;
// accs on both sides of every rounding boundary for h = 1..128 (128 = clamp edge);
// the clamp region up to 2^23-1; negatives; full-range random; the realistic range;
// the "wrap" accs where the unclamped result is exactly 2^k (k = 7..14), which a
// truncated q or product turns into a small value; and NGV golden pairs embedded
// below (section 8). Most runs are back to back (start every cycle); some have
// random idle gaps. While idle, acc carries junk, so a module that samples acc
// without start is caught.
//
// The tb's own reference reads the same quant_params.vh as the DUT, so on its own it
// cannot see a wrong QM/QSHIFT/QMAX. The embedded golden pairs come from
// host/golden.py (mem/model.json), not from quant_params.vh, and they are in this file
// rather than an external vector file so the testbench is self-contained.
//
// The verdict needs the exact number of checks: zero stimulus cannot PASS.
// No `timescale: the RTL has none, and delays here are only relative.
`default_nettype none

module tb_post;
    `include "quant_params.vh"

    localparam integer ND      = 14;     // directed values
    localparam integer NBND    = 128;    // rounding boundaries h = 1..128
    localparam integer NCLAMP  = 200;
    localparam integer NNEG    = 200;
    localparam integer NRAND   = 1000;
    localparam integer NREAL   = 1000;
    localparam integer NWRAP   = 8;      // wrap edges, k = 7..14
    localparam integer NGV     = 528;    // embedded golden.py pairs (section 8)
    localparam integer EXP_STARTS = 1 + ND + 3*NBND + 3*NWRAP + NCLAMP + NNEG + NRAND + NREAL + NGV;

    // The constants the embedded golden pairs were generated with (mem/model.json).
    localparam [23:0] GV_QM     = 24'd9065027;
    localparam integer GV_QSHIFT = 32;
    localparam [7:0]  GV_QMAX   = 8'd127;

    reg clk = 1'b0;
    always #10 clk = ~clk;

    reg               start  = 1'b0;
    reg signed [23:0] acc    = 24'sd0;
    reg        [7:0]  exp_in = 8'd0;   // expected h for the start presented this cycle

    wire [7:0] h;
    wire       done;

    post dut (.clk(clk), .start(start), .acc(acc), .h(h), .done(done));

    // ---- independent reference ------------------------------------------------
    function [7:0] ref_h(input signed [23:0] a);
        reg [63:0] r;
        begin
            if (a < 0) r = 64'd0;
            else       r = {40'd0, a};
            r = (r * QM + (64'd1 << (QSHIFT - 1))) >> QSHIFT;
            ref_h = (r > QMAX) ? QMAX : r[7:0];
        end
    endfunction

    // Smallest acc whose unclamped result is >= hh: acc*QM + 2^(S-1) >= hh*2^S.
    function [63:0] boundary(input integer hh);
        reg [63:0] num;
        begin
            num = (64'd2 * hh - 64'd1) << (QSHIFT - 1);
            boundary = (num + QM - 64'd1) / QM;
        end
    endfunction

    // ---- bookkeeping ----------------------------------------------------------
    integer errors     = 0;
    integer starts     = 0;   // starts issued
    integer checks     = 0;   // h values compared on done
    integer cyc_checks = 0;   // cycles on which done timing was checked
    integer ref_checks = 0;   // reference self-checks at boundaries
    integer py_agree   = 0;   // golden.py pairs where ref_h agreed with golden.py
    integer wrap_checks = 0;  // wrap-edge reference self-checks
    integer seed       = 32'h20261020;

    task report(input [8*24-1:0] what, input [23:0] a, input [7:0] got, input [7:0] want);
        begin
            errors = errors + 1;
            if (errors <= 10)
                $display("  mismatch %0s: acc=%0d got h=%0d done=%b, want h=%0d  (t=%0t)",
                         what, $signed(a), got, done, want, $time);
        end
    endtask

    // ---- per-cycle checker ----------------------------------------------------
    reg [2:0]  ev = 3'b000;               // start, delayed 1..3 edges
    reg [7:0]  eh0 = 0, eh1 = 0, eh2 = 0; // expected h, same delay
    reg [23:0] ea0 = 0, ea1 = 0, ea2 = 0; // acc, for messages
    reg [7:0]  last_h = 8'd0;             // h must hold this value between results

    always @(posedge clk) begin
        ev  <= {ev[1:0], start};
        eh0 <= exp_in; eh1 <= eh0; eh2 <= eh1;
        ea0 <= acc;    ea1 <= ea0; ea2 <= ea1;
    end

    // Outputs change on posedge; sample them half a cycle later.
    always @(negedge clk) begin
        cyc_checks = cyc_checks + 1;
        if (done !== ev[2])
            report(ev[2] ? "done missing" : "spurious done", ea2, h, eh2);
        if (ev[2]) begin
            checks = checks + 1;
            if (h !== eh2) report("value", ea2, h, eh2);
            last_h = h;
        end else if (h !== last_h) begin
            report("h not held", ea2, h, last_h);
            last_h = h;
        end
    end

    // ---- stimulus helpers -----------------------------------------------------
    task issue(input [23:0] a, input [7:0] e);
        begin
            @(negedge clk);
            start = 1'b1; acc = a; exp_in = e;
            starts = starts + 1;
        end
    endtask

    task issue_ref(input [23:0] a);
        issue(a, ref_h(a));
    endtask

    task idle(input integer n);
        integer k;
        for (k = 0; k < n; k = k + 1) begin
            @(negedge clk);
            start = 1'b0; acc = $random(seed); exp_in = 8'hxx;
        end
    endtask

    function [23:0] urand(input [31:0] lo, input [31:0] span);   // lo + [0, span)
        reg [31:0] r;
        begin
            r = $random(seed);
            urand = lo + ({1'b0, r[30:0]} % span);
        end
    endfunction

    // ---- the run --------------------------------------------------------------
    reg [23:0] directed [0:ND-1];
    reg [31:0] gv [0:NGV-1];
    reg [4:0]  lat;
    reg [63:0] b;
    integer    i, hh;

    // ---- embedded golden pairs: {acc[23:0], h[7:0]}, h from host/golden.py --------
    // 0..257   every place h changes over all 2^24 accs (found by evaluating golden.py's
    //          expression on the whole range), with the acc just below it; plus -2^23
    //          and 2^23-1. Independent of boundary() above.
    // 258..273 the wrap edges (unclamped result exactly 2^k, k = 7..14) and one below.
    // 274..527 the 16 test images' real layer-1 accumulators (W1 @ x + b1), 16 each.
    // Generated with Python from golden.Model() (M=9065027 SHIFT=32 QMAX=127):
    //   H = lambda a: np.minimum((np.maximum(a,0)*m.M + (1<<(m.SHIFT-1))) >> m.SHIFT, m.QMAX)
    // If the model is re-exported these go stale: the constant check in the run FAILS
    // with a message saying so, and the pairs must be regenerated.
    task load_golden;
        begin
        gv[0]=32'h80000000; gv[1]=32'h7fffff7f; gv[2]=32'h0000ec00; gv[3]=32'h0000ed01;
        gv[4]=32'h0002c601; gv[5]=32'h0002c702; gv[6]=32'h0004a002; gv[7]=32'h0004a103;
        gv[8]=32'h00067a03; gv[9]=32'h00067b04; gv[10]=32'h00085404; gv[11]=32'h00085505;
        gv[12]=32'h000a2d05; gv[13]=32'h000a2e06; gv[14]=32'h000c0706; gv[15]=32'h000c0807;
        gv[16]=32'h000de107; gv[17]=32'h000de208; gv[18]=32'h000fbb08; gv[19]=32'h000fbc09;
        gv[20]=32'h00119509; gv[21]=32'h0011960a; gv[22]=32'h00136e0a; gv[23]=32'h00136f0b;
        gv[24]=32'h0015480b; gv[25]=32'h0015490c; gv[26]=32'h0017220c; gv[27]=32'h0017230d;
        gv[28]=32'h0018fc0d; gv[29]=32'h0018fd0e; gv[30]=32'h001ad60e; gv[31]=32'h001ad70f;
        gv[32]=32'h001caf0f; gv[33]=32'h001cb010; gv[34]=32'h001e8910; gv[35]=32'h001e8a11;
        gv[36]=32'h00206311; gv[37]=32'h00206412; gv[38]=32'h00223d12; gv[39]=32'h00223e13;
        gv[40]=32'h00241713; gv[41]=32'h00241814; gv[42]=32'h0025f014; gv[43]=32'h0025f115;
        gv[44]=32'h0027ca15; gv[45]=32'h0027cb16; gv[46]=32'h0029a416; gv[47]=32'h0029a517;
        gv[48]=32'h002b7e17; gv[49]=32'h002b7f18; gv[50]=32'h002d5718; gv[51]=32'h002d5819;
        gv[52]=32'h002f3119; gv[53]=32'h002f321a; gv[54]=32'h00310b1a; gv[55]=32'h00310c1b;
        gv[56]=32'h0032e51b; gv[57]=32'h0032e61c; gv[58]=32'h0034bf1c; gv[59]=32'h0034c01d;
        gv[60]=32'h0036981d; gv[61]=32'h0036991e; gv[62]=32'h0038721e; gv[63]=32'h0038731f;
        gv[64]=32'h003a4c1f; gv[65]=32'h003a4d20; gv[66]=32'h003c2620; gv[67]=32'h003c2721;
        gv[68]=32'h003e0021; gv[69]=32'h003e0122; gv[70]=32'h003fd922; gv[71]=32'h003fda23;
        gv[72]=32'h0041b323; gv[73]=32'h0041b424; gv[74]=32'h00438d24; gv[75]=32'h00438e25;
        gv[76]=32'h00456725; gv[77]=32'h00456826; gv[78]=32'h00474126; gv[79]=32'h00474227;
        gv[80]=32'h00491a27; gv[81]=32'h00491b28; gv[82]=32'h004af428; gv[83]=32'h004af529;
        gv[84]=32'h004cce29; gv[85]=32'h004ccf2a; gv[86]=32'h004ea82a; gv[87]=32'h004ea92b;
        gv[88]=32'h0050822b; gv[89]=32'h0050832c; gv[90]=32'h00525b2c; gv[91]=32'h00525c2d;
        gv[92]=32'h0054352d; gv[93]=32'h0054362e; gv[94]=32'h00560f2e; gv[95]=32'h0056102f;
        gv[96]=32'h0057e92f; gv[97]=32'h0057ea30; gv[98]=32'h0059c330; gv[99]=32'h0059c431;
        gv[100]=32'h005b9c31; gv[101]=32'h005b9d32; gv[102]=32'h005d7632; gv[103]=32'h005d7733;
        gv[104]=32'h005f5033; gv[105]=32'h005f5134; gv[106]=32'h00612a34; gv[107]=32'h00612b35;
        gv[108]=32'h00630435; gv[109]=32'h00630536; gv[110]=32'h0064dd36; gv[111]=32'h0064de37;
        gv[112]=32'h0066b737; gv[113]=32'h0066b838; gv[114]=32'h00689138; gv[115]=32'h00689239;
        gv[116]=32'h006a6b39; gv[117]=32'h006a6c3a; gv[118]=32'h006c453a; gv[119]=32'h006c463b;
        gv[120]=32'h006e1e3b; gv[121]=32'h006e1f3c; gv[122]=32'h006ff83c; gv[123]=32'h006ff93d;
        gv[124]=32'h0071d23d; gv[125]=32'h0071d33e; gv[126]=32'h0073ac3e; gv[127]=32'h0073ad3f;
        gv[128]=32'h0075863f; gv[129]=32'h00758740; gv[130]=32'h00775f40; gv[131]=32'h00776041;
        gv[132]=32'h00793941; gv[133]=32'h00793a42; gv[134]=32'h007b1342; gv[135]=32'h007b1443;
        gv[136]=32'h007ced43; gv[137]=32'h007cee44; gv[138]=32'h007ec644; gv[139]=32'h007ec745;
        gv[140]=32'h0080a045; gv[141]=32'h0080a146; gv[142]=32'h00827a46; gv[143]=32'h00827b47;
        gv[144]=32'h00845447; gv[145]=32'h00845548; gv[146]=32'h00862e48; gv[147]=32'h00862f49;
        gv[148]=32'h00880749; gv[149]=32'h0088084a; gv[150]=32'h0089e14a; gv[151]=32'h0089e24b;
        gv[152]=32'h008bbb4b; gv[153]=32'h008bbc4c; gv[154]=32'h008d954c; gv[155]=32'h008d964d;
        gv[156]=32'h008f6f4d; gv[157]=32'h008f704e; gv[158]=32'h0091484e; gv[159]=32'h0091494f;
        gv[160]=32'h0093224f; gv[161]=32'h00932350; gv[162]=32'h0094fc50; gv[163]=32'h0094fd51;
        gv[164]=32'h0096d651; gv[165]=32'h0096d752; gv[166]=32'h0098b052; gv[167]=32'h0098b153;
        gv[168]=32'h009a8953; gv[169]=32'h009a8a54; gv[170]=32'h009c6354; gv[171]=32'h009c6455;
        gv[172]=32'h009e3d55; gv[173]=32'h009e3e56; gv[174]=32'h00a01756; gv[175]=32'h00a01857;
        gv[176]=32'h00a1f157; gv[177]=32'h00a1f258; gv[178]=32'h00a3ca58; gv[179]=32'h00a3cb59;
        gv[180]=32'h00a5a459; gv[181]=32'h00a5a55a; gv[182]=32'h00a77e5a; gv[183]=32'h00a77f5b;
        gv[184]=32'h00a9585b; gv[185]=32'h00a9595c; gv[186]=32'h00ab325c; gv[187]=32'h00ab335d;
        gv[188]=32'h00ad0b5d; gv[189]=32'h00ad0c5e; gv[190]=32'h00aee55e; gv[191]=32'h00aee65f;
        gv[192]=32'h00b0bf5f; gv[193]=32'h00b0c060; gv[194]=32'h00b29960; gv[195]=32'h00b29a61;
        gv[196]=32'h00b47361; gv[197]=32'h00b47462; gv[198]=32'h00b64c62; gv[199]=32'h00b64d63;
        gv[200]=32'h00b82663; gv[201]=32'h00b82764; gv[202]=32'h00ba0064; gv[203]=32'h00ba0165;
        gv[204]=32'h00bbda65; gv[205]=32'h00bbdb66; gv[206]=32'h00bdb466; gv[207]=32'h00bdb567;
        gv[208]=32'h00bf8d67; gv[209]=32'h00bf8e68; gv[210]=32'h00c16768; gv[211]=32'h00c16869;
        gv[212]=32'h00c34169; gv[213]=32'h00c3426a; gv[214]=32'h00c51b6a; gv[215]=32'h00c51c6b;
        gv[216]=32'h00c6f46b; gv[217]=32'h00c6f56c; gv[218]=32'h00c8ce6c; gv[219]=32'h00c8cf6d;
        gv[220]=32'h00caa86d; gv[221]=32'h00caa96e; gv[222]=32'h00cc826e; gv[223]=32'h00cc836f;
        gv[224]=32'h00ce5c6f; gv[225]=32'h00ce5d70; gv[226]=32'h00d03570; gv[227]=32'h00d03671;
        gv[228]=32'h00d20f71; gv[229]=32'h00d21072; gv[230]=32'h00d3e972; gv[231]=32'h00d3ea73;
        gv[232]=32'h00d5c373; gv[233]=32'h00d5c474; gv[234]=32'h00d79d74; gv[235]=32'h00d79e75;
        gv[236]=32'h00d97675; gv[237]=32'h00d97776; gv[238]=32'h00db5076; gv[239]=32'h00db5177;
        gv[240]=32'h00dd2a77; gv[241]=32'h00dd2b78; gv[242]=32'h00df0478; gv[243]=32'h00df0579;
        gv[244]=32'h00e0de79; gv[245]=32'h00e0df7a; gv[246]=32'h00e2b77a; gv[247]=32'h00e2b87b;
        gv[248]=32'h00e4917b; gv[249]=32'h00e4927c; gv[250]=32'h00e66b7c; gv[251]=32'h00e66c7d;
        gv[252]=32'h00e8457d; gv[253]=32'h00e8467e; gv[254]=32'h00ea1f7e; gv[255]=32'h00ea207f;
        gv[256]=32'h00ebf87f; gv[257]=32'h00ebf97f; gv[258]=32'h01d8de7f; gv[259]=32'h01d8df7f;
        gv[260]=32'h03b2aa7f; gv[261]=32'h03b2ab7f; gv[262]=32'h0766417f; gv[263]=32'h0766427f;
        gv[264]=32'h0ecd6f7f; gv[265]=32'h0ecd707f; gv[266]=32'h1d9bcc7f; gv[267]=32'h1d9bcd7f;
        gv[268]=32'h3b38867f; gv[269]=32'h3b38877f; gv[270]=32'h7671f97f; gv[271]=32'h7671fa7f;
        gv[272]=32'h00297716; gv[273]=32'h0050182b; gv[274]=32'h00257d14; gv[275]=32'h0056dc2f;
        gv[276]=32'h0041bc24; gv[277]=32'h002b2917; gv[278]=32'h0004f903; gv[279]=32'h001bf00f;
        gv[280]=32'h00102a09; gv[281]=32'h0002b301; gv[282]=32'h00272115; gv[283]=32'h00167b0c;
        gv[284]=32'h00201311; gv[285]=32'h00451625; gv[286]=32'h0004a403; gv[287]=32'hfff8cb00;
        gv[288]=32'h003b6d20; gv[289]=32'hfff50300; gv[290]=32'hffc01800; gv[291]=32'h002b2f17;
        gv[292]=32'hffef0f00; gv[293]=32'hfff39f00; gv[294]=32'h001de810; gv[295]=32'h0039c41f;
        gv[296]=32'h0016350c; gv[297]=32'h00402623; gv[298]=32'hffebce00; gv[299]=32'hffd4c000;
        gv[300]=32'h0070a43d; gv[301]=32'h006e353c; gv[302]=32'h00502b2b; gv[303]=32'h0089094a;
        gv[304]=32'h000eed08; gv[305]=32'hfff8b600; gv[306]=32'h0018ec0d; gv[307]=32'hfffd8c00;
        gv[308]=32'h00254614; gv[309]=32'h0004d603; gv[310]=32'hffe14700; gv[311]=32'hfffc0800;
        gv[312]=32'h0013320a; gv[313]=32'h001f2b11; gv[314]=32'h0026c115; gv[315]=32'h00118709;
        gv[316]=32'h00272515; gv[317]=32'h0007a704; gv[318]=32'h00285516; gv[319]=32'h0025c114;
        gv[320]=32'h0012410a; gv[321]=32'h004ea92b; gv[322]=32'h001b460f; gv[323]=32'h001dc310;
        gv[324]=32'h001e5910; gv[325]=32'hfff4af00; gv[326]=32'h0038161e; gv[327]=32'h006dc63b;
        gv[328]=32'h00267d15; gv[329]=32'h001be50f; gv[330]=32'hffea5f00; gv[331]=32'hfffd9a00;
        gv[332]=32'h0008a905; gv[333]=32'h0090d94e; gv[334]=32'h0001f601; gv[335]=32'h00605534;
        gv[336]=32'hfff2ac00; gv[337]=32'h003d6421; gv[338]=32'h00075804; gv[339]=32'h00005200;
        gv[340]=32'h000e1b08; gv[341]=32'h00011b01; gv[342]=32'h00032702; gv[343]=32'h0037d51e;
        gv[344]=32'h00270015; gv[345]=32'h0037511e; gv[346]=32'h001ada0f; gv[347]=32'h00241e14;
        gv[348]=32'hfff5f000; gv[349]=32'h0018e50d; gv[350]=32'hffdc5700; gv[351]=32'h000dbb07;
        gv[352]=32'h000fa408; gv[353]=32'h00051b03; gv[354]=32'h00280a16; gv[355]=32'h000b2e06;
        gv[356]=32'h0039541f; gv[357]=32'h0002e002; gv[358]=32'hffd19d00; gv[359]=32'hfff9b300;
        gv[360]=32'h0013040a; gv[361]=32'h00222f12; gv[362]=32'h003d0321; gv[363]=32'h00195e0e;
        gv[364]=32'h00338f1c; gv[365]=32'h00054003; gv[366]=32'h00323c1b; gv[367]=32'h0029fc17;
        gv[368]=32'h000b3806; gv[369]=32'h00596130; gv[370]=32'h00068904; gv[371]=32'h00019c01;
        gv[372]=32'h001f4911; gv[373]=32'hffed9500; gv[374]=32'h0010aa09; gv[375]=32'h003ad420;
        gv[376]=32'h00433524; gv[377]=32'h0029e117; gv[378]=32'h002b0517; gv[379]=32'h00412c23;
        gv[380]=32'hfff28200; gv[381]=32'h0017af0d; gv[382]=32'h0014940b; gv[383]=32'hfffa4900;
        gv[384]=32'h0008bd05; gv[385]=32'h003a321f; gv[386]=32'h0024a314; gv[387]=32'h000a4606;
        gv[388]=32'h000dda07; gv[389]=32'h0012c20a; gv[390]=32'h00002a00; gv[391]=32'h002ef219;
        gv[392]=32'h0011ba0a; gv[393]=32'h002e9719; gv[394]=32'h0034261c; gv[395]=32'h003a161f;
        gv[396]=32'hffef7000; gv[397]=32'hffeecc00; gv[398]=32'h002ce818; gv[399]=32'h0034851c;
        gv[400]=32'h00116609; gv[401]=32'h00228713; gv[402]=32'h000f5d08; gv[403]=32'hffcd4400;
        gv[404]=32'hfffe2600; gv[405]=32'h000cb707; gv[406]=32'hffc24d00; gv[407]=32'h0068d039;
        gv[408]=32'h005b4331; gv[409]=32'h00400a23; gv[410]=32'hffeae200; gv[411]=32'h00271415;
        gv[412]=32'hfffd0000; gv[413]=32'h00429724; gv[414]=32'hfff14400; gv[415]=32'h004fc32b;
        gv[416]=32'hffe9d400; gv[417]=32'h007c8d43; gv[418]=32'h00406b23; gv[419]=32'h00235313;
        gv[420]=32'h00478027; gv[421]=32'hfff61e00; gv[422]=32'h0016680c; gv[423]=32'h00472226;
        gv[424]=32'h00461f26; gv[425]=32'h00239c13; gv[426]=32'h00287916; gv[427]=32'h00452f25;
        gv[428]=32'hffedf600; gv[429]=32'h002bc218; gv[430]=32'h00021501; gv[431]=32'h00267d15;
        gv[432]=32'h0019530e; gv[433]=32'h005e1b33; gv[434]=32'hffc75600; gv[435]=32'h00025f01;
        gv[436]=32'hfffd4a00; gv[437]=32'hfff87900; gv[438]=32'h0021ae12; gv[439]=32'h0057c52f;
        gv[440]=32'h001bba0f; gv[441]=32'h0014b30b; gv[442]=32'hffd2f800; gv[443]=32'h0002f602;
        gv[444]=32'h0030f31a; gv[445]=32'h00781141; gv[446]=32'h0005e103; gv[447]=32'h003f0f22;
        gv[448]=32'hffe75200; gv[449]=32'h002aa917; gv[450]=32'hffdfb900; gv[451]=32'hfffe0d00;
        gv[452]=32'h00274715; gv[453]=32'hffe1dc00; gv[454]=32'h000e8608; gv[455]=32'h003dc421;
        gv[456]=32'h0035541d; gv[457]=32'h00440225; gv[458]=32'h0004cb03; gv[459]=32'hfffe8000;
        gv[460]=32'h00156b0c; gv[461]=32'h003b4f20; gv[462]=32'h0014e50b; gv[463]=32'h0044e825;
        gv[464]=32'h000ad206; gv[465]=32'h00613b35; gv[466]=32'h002fea1a; gv[467]=32'h002b1d17;
        gv[468]=32'h002a2317; gv[469]=32'h000ef608; gv[470]=32'h000c6c07; gv[471]=32'h00433c24;
        gv[472]=32'h002a0717; gv[473]=32'h00245114; gv[474]=32'h002ecc19; gv[475]=32'h002fed1a;
        gv[476]=32'hffff3700; gv[477]=32'h001fd911; gv[478]=32'h0008c705; gv[479]=32'h001b850f;
        gv[480]=32'h000b5306; gv[481]=32'h0074543f; gv[482]=32'hfff13000; gv[483]=32'h001d4510;
        gv[484]=32'hfff24e00; gv[485]=32'hfffc3200; gv[486]=32'h003b9220; gv[487]=32'h005b5531;
        gv[488]=32'h000c1307; gv[489]=32'h00038a02; gv[490]=32'hfff04000; gv[491]=32'h0016ef0c;
        gv[492]=32'h0014160b; gv[493]=32'h00646336; gv[494]=32'hfff2d100; gv[495]=32'h0043bb25;
        gv[496]=32'h00243714; gv[497]=32'h00048802; gv[498]=32'h002ba718; gv[499]=32'h0012ca0a;
        gv[500]=32'h0043be25; gv[501]=32'hfffdf000; gv[502]=32'hffdec700; gv[503]=32'h0008c305;
        gv[504]=32'h0016550c; gv[505]=32'h002c4f18; gv[506]=32'h003cfc21; gv[507]=32'h0015730c;
        gv[508]=32'h0033d41c; gv[509]=32'hffffc200; gv[510]=32'h00580530; gv[511]=32'h00447f25;
        gv[512]=32'h003a6d20; gv[513]=32'h0036ba1e; gv[514]=32'hffd80a00; gv[515]=32'hffffe600;
        gv[516]=32'hffedb500; gv[517]=32'hffe02900; gv[518]=32'h004fd92b; gv[519]=32'h00280516;
        gv[520]=32'h001f5711; gv[521]=32'h001b610f; gv[522]=32'h000b5a06; gv[523]=32'h001e4310;
        gv[524]=32'h00116109; gv[525]=32'h003bbb20; gv[526]=32'h0034d91d; gv[527]=32'h00202611;
        end
    endtask

    initial begin
        directed[0]  = 24'd0;         directed[1]  = 24'd1;
        directed[2]  = -24'sd1;       directed[3]  = 24'd2;
        directed[4]  = -24'sd2;       directed[5]  = 24'h800000;     // -2^23
        directed[6]  = 24'h7FFFFF;    directed[7]  = 24'h7FFFFE;     // max acc
        directed[8]  = 24'h400000;    directed[9]  = 24'd237;
        directed[10] = 24'd65478;     directed[11] = 24'd60000;
        directed[12] = 24'd100000;    directed[13] = -24'sd65478;

        idle(3);

        // 1. One isolated start: done exactly 3 cycles later, exactly 1 cycle wide.
        issue_ref(24'd5000);
        for (i = 0; i < 5; i = i + 1) begin
            @(negedge clk);
            start = 1'b0; acc = $random(seed);
            lat[i] = done;
        end
        if (lat !== 5'b00100) begin
            errors = errors + 1;
            $display("  latency: done over the 5 cycles after start = %b (bit i = cycle i+1), want 00100", lat);
        end

        // 2. Directed values, isolated.
        for (i = 0; i < ND; i = i + 1) begin
            issue_ref(directed[i]);
            idle(4);
        end

        // 3. Every rounding boundary, back to back. The reference is checked at
        //    each one too, so a wrong boundary formula cannot hide a weak test.
        for (hh = 1; hh <= NBND; hh = hh + 1) begin
            b = boundary(hh);
            ref_checks = ref_checks + 1;
            if (ref_h(b[23:0] - 24'd1) !== (hh - 1) || ref_h(b[23:0]) !== ((hh > 127) ? 127 : hh)) begin
                errors = errors + 1;
                $display("  reference self-check failed at h=%0d, acc=%0d", hh, b);
            end
            issue_ref(b[23:0] - 24'd1);
            issue_ref(b[23:0]);
            issue_ref(b[23:0] + 24'd1);
        end
        idle(2);

        // 3b. Wrap edges, back to back: the smallest acc whose unclamped result is
        //     exactly 2^k, k = 7..14 (2^14 is the top bit of q at acc = 2^23-1), and
        //     the smallest acc whose product acc*QM reaches 2^(k+QSHIFT). A q cut to
        //     k bits gives 0 at the first, a product cut to k+QSHIFT bits gives ~0 at
        //     the second, instead of the clamp. Random stimulus only hits the narrow
        //     band above each edge by luck.
        for (hh = 7; hh < 7 + NWRAP; hh = hh + 1) begin
            b = boundary(1 << hh);
            wrap_checks = wrap_checks + 1;
            if (((b * QM + (64'd1 << (QSHIFT - 1))) >> QSHIFT) !== (64'd1 << hh) || b > 24'h7FFFFF) begin
                errors = errors + 1;
                $display("  wrap self-check failed at k=%0d, acc=%0d", hh, b);
            end
            issue_ref(b[23:0] - 24'd1);
            issue_ref(b[23:0]);
            b = ((64'd1 << (hh + QSHIFT)) + QM - 64'd1) / QM;   // ceil(2^(k+QSHIFT) / QM)
            if (b * QM < (64'd1 << (hh + QSHIFT)) || (b - 64'd1) * QM >= (64'd1 << (hh + QSHIFT)) || b > 24'h7FFFFF) begin
                errors = errors + 1;
                $display("  product-wrap self-check failed at k=%0d, acc=%0d", hh, b);
            end
            issue_ref(b[23:0]);
        end
        idle(2);

        // 4. Clamp region up to 2^23-1, back to back.
        b = boundary(128);
        for (i = 0; i < NCLAMP; i = i + 1)
            issue_ref((i == 0) ? 24'h7FFFFF : urand(b[31:0], 32'h800000 - b[31:0]));
        idle(2);

        // 5. Negatives, random gaps.
        for (i = 0; i < NNEG; i = i + 1) begin
            issue_ref((i == 0) ? 24'h800000 : -urand(1, 32'h800000));
            idle($random(seed) & 3);
        end

        // 6. Full 24-bit random, random gaps.
        for (i = 0; i < NRAND; i = i + 1) begin
            issue_ref($random(seed));
            idle($random(seed) & 3);
        end

        // 7. Realistic layer-1 range (observed |acc| <= 65,478), back to back.
        for (i = 0; i < NREAL; i = i + 1)
            issue_ref(urand(32'hFFFE0000, 32'h40000));   // -2^17 .. 2^17-1
        idle(2);

        // 8. Embedded golden.py pairs, back to back. The DUT is checked against
        //    golden.py's h, not ref_h, so a wrong quant_params.vh shows up here.
        if (QM !== GV_QM || QSHIFT !== GV_QSHIFT || QMAX !== GV_QMAX) begin
            errors = errors + 1;
            $display("  quant_params.vh (QM=%0d QSHIFT=%0d QMAX=%0d) differs from the constants the embedded golden pairs were made with (%0d %0d %0d): regenerate them",
                     QM, QSHIFT, QMAX, GV_QM, GV_QSHIFT, GV_QMAX);
        end
        for (i = 0; i < NGV; i = i + 1) gv[i] = 32'hxxxxxxxx;
        load_golden;
        for (i = 0; i < NGV; i = i + 1) begin
            if (^gv[i] === 1'bx) begin
                errors = errors + 1;
                if (errors <= 10) $display("  golden vector %0d missing", i);
            end else begin
                if (ref_h(gv[i][31:8]) === gv[i][7:0]) py_agree = py_agree + 1;
                else report("tb ref vs golden.py", gv[i][31:8], ref_h(gv[i][31:8]), gv[i][7:0]);
                issue(gv[i][31:8], gv[i][7:0]);
            end
        end

        idle(6);   // drain the pipeline

        $display("post: %0d starts (want %0d), %0d values checked, %0d cycles timed, %0d boundary + %0d wrap self-checks, %0d/%0d golden.py pairs agree, %0d errors",
                 starts, EXP_STARTS, checks, cyc_checks, ref_checks, wrap_checks, py_agree, NGV, errors);
        if (errors == 0 && starts == EXP_STARTS && checks == EXP_STARTS &&
            ref_checks == NBND && wrap_checks == NWRAP && py_agree == NGV && cyc_checks > EXP_STARTS)
            $display("PASS");
        else
            $display("FAIL");
        $finish;
    end
endmodule

`default_nettype wire
