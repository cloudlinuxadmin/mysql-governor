CMAKE_MINIMUM_REQUIRED (VERSION 3.12)
SET(CMAKE_VERBOSE_MAKEFILE ON)

PROJECT("klee_tests")

SET(CMAKE_C_FLAGS "-emit-llvm -g -D_GNU_SOURCE -D__USE_GNU -c")
SET(CMAKE_CXX_FLAGS "-emit-llvm -g -D_GNU_SOURCE -D__USE_GNU -c")
SET(CMAKE_C_COMPILER "clang")
SET(CMAKE_CXX_COMPILER "clang++")
SET(CMAKE_C_LINK_EXECUTABLE "llvm-link <OBJECTS> -o <TARGET> <LINK_LIBRARIES>")
SET(CMAKE_CXX_LINK_EXECUTABLE "llvm-link  <OBJECTS> -o <TARGET> <LINK_LIBRARIES>")

INCLUDE(CheckFunctionExists)

CHECK_FUNCTION_EXISTS (mmap64 HAVE_MMAP64)

SET(CMAKE_BUILD_TYPE Debug)
SET(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#SET(MYSQL_INCLUDE_DIRS "/usr/include/mysql")
FIND_PACKAGE(GLIB2 REQUIRED)
FIND_PACKAGE(LibXml2 REQUIRED)
#FIND_PACKAGE(MySQL REQUIRED)

#INCLUDE_DIRECTORIES(${GLIB2_INCLUDE_DIRS} ${MYSQL_INCLUDE_DIRS})
INCLUDE_DIRECTORIES(${GLIB2_INCLUDE_DIRS})
INCLUDE_DIRECTORIES(${LIBXML2_INCLUDE_DIR})
#LINK_LIBRARIES(${GLIB2_LIBRARIES} ${MYSQL_CLIENT_LIBS})
#INCLUDE_DIRECTORIES(${GLIB2_INCLUDE_DIRS})

# ELF format, not compatible with LLVM. Is it crucial?
#LINK_LIBRARIES(${GLIB2_LIBRARIES})
#LINK_LIBRARIES(${LIBXML2_LIBRARIES})
#LINK_LIBRARIES(pthread)
#LINK_LIBRARIES(m)
#LINK_LIBRARIES(rt)
#LINK_LIBRARIES(dl)
#LINK_LIBRARIES(ncurses)

IF (${SYSTEMD_FLAG})
    add_definitions(-DSYSTEMD_FLAG=1)
    LINK_LIBRARIES(systemd)
ENDIF(${SYSTEMD_FLAG})

SET(LIBSRC "../../src")
FILE(GLOB MOCK_FILES RELATIVE ${CMAKE_SOURCE_DIR} "${CMAKE_SOURCE_DIR}/mock/*.c")
MESSAGE(STATUS "******* Mock files is use: ${MOCK_FILES} *******")

ADD_LIBRARY(objects OBJECT
${LIBSRC}/calc_stats.c
${LIBSRC}/commands.c
${LIBSRC}/dbctl_cfg.c
${LIBSRC}/dbctl_conn.c
${LIBSRC}/dbctl_list.c
${LIBSRC}/dbctl_rest.c
${LIBSRC}/dbctl_set.c
${LIBSRC}/dbgovernor_string_functions.c
${LIBSRC}/dbtop_server.c
${LIBSRC}/dbuser_map.c
${LIBSRC}/dlload.c
${LIBSRC}/fifo_stats.c
${LIBSRC}/getsysinfo.c
${LIBSRC}/governor_config.c
${LIBSRC}/governor_server.c
${LIBSRC}/governor_write_data.c
${LIBSRC}/log.c
${LIBSRC}/log-decoder.c
${LIBSRC}/mysql_connector_common.c
${LIBSRC}/parce_proc_fs.c
${LIBSRC}/shared_memory.c
${LIBSRC}/slow_queries.c
${LIBSRC}/stats.c
${LIBSRC}/tick_generator.c
${LIBSRC}/tid_table.c
${LIBSRC}/user_account.c
${LIBSRC}/wrappers.c
${LIBSRC}/xml.c
# These ones contain main function
#${LIBSRC}/dbctl.c
#${LIBSRC}/dbtop.c
#${LIBSRC}/governor.c
#${LIBSRC}/mysql_unfreeze.c
${MOCK_FILES}
)

ADD_CUSTOM_TARGET(test "${CMAKE_SOURCE_DIR}/scripts/run_suites.py" WORKING_DIRECTORY "${CMAKE_BINARY_DIR}" VERBATIM)
ADD_SUBDIRECTORY(suites)

ADD_CUSTOM_TARGET(
    clean_test
    COMMAND rm -f CMakeCache.txt cmake_install.cmake Makefile suites/CMakeCache.txt suites/cmake_install.cmake suites/Makefile
    COMMAND rm -rf CMakeFiles suites/CMakeFiles
    COMMAND rm -f suites/*_test.bc
    COMMAND rm -rf suites/*_test
)
