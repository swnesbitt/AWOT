      SUBROUTINE SIDE2(A_IN,SD_A_IN,NX,BADDATA,MAX_SEARCH_RADIUS,
     $MAX_VALUES_PER_SIDE,IX,POINTS_FOUND,IX_FOUND)

      IMPLICIT NONE
      INTEGER NX,IX,IX_SEARCH,POINTS_FOUND,MAX_SEARCH_RADIUS,
     $MAX_VALUES_PER_SIDE
      INTEGER IX_FOUND(1)
      REAL BADDATA
      REAL A_IN(NX),SD_A_IN(NX)

      POINTS_FOUND=0
      DO 1 IX_SEARCH=IX+1,IX+MAX_SEARCH_RADIUS
         IF(IX_SEARCH.GT.NX)THEN
            GOTO 3
         ENDIF
         IF(A_IN(IX_SEARCH).NE.BADDATA.AND.
     $   SD_A_IN(IX_SEARCH).NE.BADDATA)THEN
            POINTS_FOUND=POINTS_FOUND+1
            IX_FOUND(POINTS_FOUND)=IX_SEARCH
            IF(POINTS_FOUND.GE.MAX_VALUES_PER_SIDE)THEN
               RETURN
            ENDIF
         ENDIF
3        CONTINUE
1     CONTINUE
      RETURN
      END
