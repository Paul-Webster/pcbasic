10 SCREEN 0,1:WIDTH 80
20 ON ERROR GOTO 480
30 IF ABC$<>"" THEN 50
40 TF=7:TB=1:MF=4:MB=2:N=4:X=9:Y=30:IF EFG$<>"" THEN N=10:X=5:Y=20
50 IF LIO$="1" THEN TF=4:TB=2:MF=7:MB=1:N=4:X=9:Y=30:IF EFG$<>"" THEN N=10:X=5:Y=20
60 COLOR TF,TB:CLS:KEY OFF:DIM M$(N),FC(N),BC(N)
70 IF C=0 THEN C=1
80 IF ACD$<>"" AND N$(1)<>"" THEN FOR T=1 TO N:M$(T)=N$(T):NEXT T:GOTO 110
90 M$(1)="  1.  选项一    ":M$(2)="  2.  选项三    "
100 M$(3)="  3.  选项三    ":M$(4)="  4.  选项四    "
110 IF EFG$="" THEN LOCATE 4,34:PRINT "Main  Menu":LOCATE X-3,Y+1:PRINT "Setup  selection":LOCATE 20,23:PRINT "INS=Change color, ESC=Exit setup";
120 IF EFG$="" THEN L=16 ELSE L=43
130 FOR J=1 TO N:LOCATE X+J,Y+1:PRINT M$(J)+SPACE$(L-LEN(M$(J))):NEXT J
140 COLOR MF,MB:LOCATE X,Y:PRINT CHR$(218);STRING$(L,CHR$(196));CHR$(191)
150 FOR J=1 TO N:COLOR MF,MB:LOCATE X+J,Y
160 PRINT CHR$(179);M$(J);CHR$(179);:COLOR 0,0:PRINT "":NEXT J
170 LOCATE X+N+1,Y:COLOR MF,MB:PRINT CHR$(192);STRING$(L,CHR$(196));CHR$(217)
180 COLOR 0,0:PRINT:LOCATE X+N+2,Y+2:COLOR 0,0:PRINT SPACE$(L+2)
190 FOR Z=1 TO N+1:LOCATE X+Z,Y+L+2:PRINT SPACE$(2):NEXT Z
200 FOR J=1 TO N:FC(J)=MF:BC(J)=MB:NEXT J:FC(C)=MB:BC(C)=MF:GOTO 380
210 A$=INKEY$::IF A$="" THEN GOSUB 460:GOTO 210
220 IF A$=CHR$(13) THEN 420
230 IF A$=CHR$(27) OR A$=CHR$(21) THEN C=0:GOTO 420
240 IF EFG$="" AND A$=CHR$(0)+CHR$(82) THEN IF CCA$<>"1" THEN ABC$="A":LIO$="1":CCA$="1":GOTO 30 ELSE LIO$="0":ABC$="":CCA$="":GOTO 30
250 IF EFG$<>"" AND A$=CHR$(0)+CHR$(82) THEN IF CCA$<>"1" THEN ABC$="A":LIO$="1":CCA$="1":GOTO 40 ELSE LIO$="0":ABC$="":CCA$="":GOTO 40
260 FOR J=1 TO N:IF A$<>CHR$(0)+CHR$(72) OR BC(J)=MB THEN 300
270 IF J=1 THEN SWAP FC(1),FC(N):SWAP BC(1),BC(N):C=N
280 IF J>1 THEN SWAP FC(J),FC(J-1):SWAP BC(J),BC(J-1):C=J-1
290 GOTO 380
300 IF A$<>CHR$(0)+CHR$(80) OR BC(J)=MB THEN 340
310 IF J=N THEN SWAP FC(1),FC(N):SWAP BC(1),BC(N):C=1
320 IF J<N THEN SWAP FC(J),FC(J+1):SWAP BC(J),BC(J+1):C=J+1
330 GOTO 380
340 V=VAL(A$):IF EFG$<>"" THEN IF V>0 AND V<=N THEN C=V:GOTO 420
350 IF EFG$="" THEN IF V>0 AND V<5 THEN C=V:GOTO 420
360 IF A$="0" THEN C=0:GOTO 420
370 NEXT J:KEY OFF:GOSUB 460
380 COLOR TF,TB:IF EFG$="" THEN KEY OFF:LOCATE 17,35:PRINT "Choice:";
390 IF EFG$<>"" THEN COLOR 7,0:LOCATE 18,54:IF C=10 THEN C=0
400 PRINT C;:IF EFG$<>"" AND C=0 THEN C=10
410 FOR J=1 TO N:LOCATE X+J,Y+1:COLOR FC(J),BC(J):PRINT M$(J):NEXT J:GOTO 210
420 ERASE M$,FC,BC
430 COLOR TF,TB:LOCATE X+N+4,Y:IF EFG$="" THEN 500
440 IF BCD$="" THEN COLOR 7,0 ELSE RETURN
450 GOTO 30
460 IF EFG$<>"" THEN LOCATE 25,33 ELSE LOCATE 25,31
470 end:COLOR TF,TB:PRINT "Time is: ";TIME$;"  ";:RETURN
480 ON ERROR GOTO 480:RESUME NEXT
490 GOTO 30
500 COLOR 7,0:CLS:PRINT "The choice is";STR$(C);".":C=0:KEY ON
