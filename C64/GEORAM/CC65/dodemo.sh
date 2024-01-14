cl65 demo.c -o demo.prg
export C1541=/Users/yourname/Desktop/vice-x86-64-gtk3-3.7.1/bin/c1541 
$C1541 -format "georam-demo,00" d64 demo.d64
$C1541 -attach demo.d64 -write demo.prg 
$C1541 -attach demo.d64 -write c64-georam.emd
