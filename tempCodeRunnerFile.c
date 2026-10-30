#include <stdio.h>
#include <string.h>
#include <stddef.h>
size_t count_chars(const char *text){
    size_t cnt=0;
    while(text[cnt]){
        cnt++;
    }
    return cnt;
}
int copy_text(char *dest, size_t capacity, const char *src){

    int n=strlen(src);
    if(capacity<=n||dest==NULL)return -1;
    size_t cnt=0;
    do{
       dest[cnt]=src[cnt];
    }while(src[cnt++]!='\0');
    return 0;

}

int main(void)
{
    

 
      char source[] = "systems";
    char destination[10];

    printf("Length: %zu\n", count_chars(source));

    if (copy_text(destination, sizeof destination, source) == 0) {
        printf("Copied: %s\n", destination);
    } else {
        printf("Copy failed\n");
    }

    return 0;
}