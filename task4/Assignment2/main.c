#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

extern unsigned elemNum;
extern void assign_malloc (void*, unsigned);

int main (int argc, char ** argv)
{
    int * alloc= malloc(sizeof(int) * elemNum); 
    
    assign_malloc (alloc, elemNum+1); 

    int * temp= alloc + 3;
    printf("> main -- alloc[3]: %d\n", *temp);
    
    temp= temp + 1; 
    printf("> main -- alloc[4]: %d\n", *temp);
    
    //temp= temp + 1;   //comment out
    *temp = 20;         //insert a store instruction
    /* out of bounds */
    printf("> main-- alloc[5]: %d <--- buffer overflow\n", *temp);
    printf("> main-- alloc+22: %d <--- buffer overflow\n", *(alloc+22));
     
    free(alloc);

    return 0;
}

