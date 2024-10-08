REM 
REM I2C TIME SERVER DEMO / SLAVE
REM 


REM 
REM WHEN NEW BYTES ARE AVAILABLE FROM I2C, THIS
REM SUBROUTINE WILL BE CALLED
REM 

SUB RINT
    LOCAL COUNT, A$
    I2C SLAVE READ 10, A$, COUNT
    PRINT "FROM I2C MASTER:";LEFT$(A$, COUNT)
END SUB

REM
REM WHEN THE MASTER REQUESTS DATA FROM SLAVE
REM THIS SUBROUTINE WILL BE CALLED
REM 

SUB TINT
    LOCAL A$=TIME$
    I2C SLAVE WRITE LEN(A$), A$
END SUB


REM 
REM THE SLAVE USES THE SAME HARDWARE USED BY THE 
REM MASTER ON DIFFERENS PINS
REM  
SETPIN GP8, GP9, I2C

REM 
REM PLEASE NOTE: EACH SLAVE IS SUPPOSED TO OWN 
REM AN UNIQUE ADDRESS, IN THIS CASE IT IS $50
REM IN THE OPENING COMMAND, WE NEED TO PROVIDED 
REM THE CALLBACKS NAMES
REM  
I2C SLAVE OPEN &H50, TINT, RINT

REM 
REM IN THIS CASE, THE SLAVE WILL WAIT FOR THE 
REM MASTER COMMAND DOING NOTHING MEANWHILE.
REM 

PRINT "I2C SLAVE ECHO TIME STARTED, CTRL+C TO END"
DO :LOOP

