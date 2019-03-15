#include <klee/klee.h>

#include <xml.h>

int main() {
    uint64_t ptr;
    char error_buf[MAX_XML_PATH];
    klee_make_symbolic(error_buf, sizeof(error_buf), "error_buf");
    klee_make_symbolic(&ptr, sizeof(uint64_t), "ptr");

    ptr = (uint64_t)parseConfigData("./mysql_governor.xml", error_buf, MAX_XML_PATH - 1);

    return 0;
}
