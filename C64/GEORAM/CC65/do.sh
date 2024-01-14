cl65 test.c -o test.prg
export C1541=/Users/yourname/Desktop/vice-x86-64-gtk3-3.7.1/bin/c1541 
$C1541 -format "georam-test,00" d64 disk.d64
$C1541 -attach disk.d64 -write test.prg 
$C1541 -attach disk.d64 -write c64-georam.emd
