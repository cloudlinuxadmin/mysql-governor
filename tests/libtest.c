#include <stdio.h>
#include <dlfcn.h>
#include <unistd.h>

volatile int governor_get_command = 0;
int (*connect_to_server)() = NULL;
int (*send_info_begin)(char *) = NULL;
int (*send_info_end)(char *) = NULL;
int (*close_sock)() = NULL;
void * governor_library_handle = NULL;

int main(){
  governor_get_command = 1;
  connect_to_server = NULL;
  send_info_begin = NULL;
  send_info_end = NULL;
  close_sock = NULL;
  governor_library_handle = NULL;

  char *error_dl = NULL;
  governor_library_handle = dlopen("/root/msql/governor-new/lib/libgovernor.so", RTLD_LAZY);
  if (governor_library_handle) {
      while(1){
	  connect_to_server = (int (*)())dlsym(governor_library_handle, "connect_to_server");
	  if ((error_dl = dlerror()) != NULL){
	      connect_to_server = NULL;
	      send_info_begin = NULL;
	      send_info_end = NULL;
	      close_sock = NULL;
	      break;
	  }
	  send_info_begin = (int (*)(char *))dlsym(governor_library_handle, "send_info_begin");
	  if ((error_dl = dlerror()) != NULL){
	      connect_to_server = NULL;
	      send_info_begin = NULL;
	      send_info_end = NULL;
	      close_sock = NULL;
	      break;
	  }
	  send_info_end = (int (*)(char *))dlsym(governor_library_handle, "send_info_end");
	  if ((error_dl = dlerror()) != NULL){
	      connect_to_server = NULL;
	      send_info_begin = NULL;
	      send_info_end = NULL;
	      close_sock = NULL;
	      break;
	  }
	  close_sock = (int (*)())dlsym(governor_library_handle, "close_sock");
	  if ((error_dl = dlerror()) != NULL){
	      connect_to_server = NULL;
	      send_info_begin = NULL;
	      send_info_end = NULL;
	      close_sock = NULL;
	      break;
	  }
	  break;
      }
  }
  if(connect_to_server){
      (*connect_to_server)();
  }

  if(send_info_begin&&governor_get_command){
      
	  (*send_info_begin)("test2");
      
  }

  printf("Ok\n");
  sleep(10);

  if(send_info_end&&governor_get_command){
    
      (*send_info_end)("test2");
    
  }

  if(close_sock){
    (*close_sock)();
  }

    return 0;
}
