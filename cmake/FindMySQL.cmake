##############################################################################
# Try to find MySQL include dirs ad libraries
##############################################################################
#
# Usage of this module as follows:
#
#   find_package( MySQL )
#   if(MySQL_FOUND)
#     include_directories(${MySQL_INCLUDE_DIRS})
#     add_executable(foo foo.cc)
#   endif()
#
#
##############################################################################
#
# Variables used by this module, they can change the default behaviour and
# need to set before calling find_package:
#
#   MYSQL_INCLUDEDIR             Set this to the include directory of MySQL.
#   MYSQL_LIBRARYDIR             Set this to the lib directory of MySQL.
#
#
##############################################################################
#
# Variables defined by this module.
#
#  MySQL_FOUND                   System has MySQL, this means the include dir
#                                was found as well as the library.
#  MySQL_INCLUDE_DIR             MySQL include directory.
#  MySQL_LIBRARIES               Link to this to use the MySQL library.
#  MySQL_MAJOR_VERSION           Major version number of MySQL.
#  MySQL_MINOR_VERSION           Minor version number of MySQL.
#  MySQL_PLUGIN_DIR              Plugin directory.
#  MySQL_VERSION                 The version numer of MySQL.
#
#
##############################################################################
#
# Copyright (c) 2006, Jaroslaw Staniek, <js@iidea.pl>
# Copyright (c) 2010, CNRS
#
# Redistribution and use is allowed according to the terms of the BSD license.
# For details see the accompanying COPYING-CMAKE-SCRIPTS file.
#
##############################################################################


if(UNIX)
    set(MYSQL_CONFIG_PREFER_PATH "$ENV{MYSQL_HOME}/bin" CACHE FILEPATH
        "preferred path to MySQL (mysql_config)")
    find_program(MYSQL_CONFIG mysql_config
                 ${MYSQL_CONFIG_PREFER_PATH}
                 /usr/local/mysql/bin/
                 /usr/local/bin/
                 /usr/bin/
    )

    if(MYSQL_CONFIG)
        message(STATUS "Using mysql-config: ${MYSQL_CONFIG}")

        # set INCLUDE_DIR
        exec_program(${MYSQL_CONFIG}
                     ARGS --include
                     OUTPUT_VARIABLE MY_TMP)
        string(REGEX REPLACE "-I([^ ]+)( .*)?" "\\1" MY_TMP "${MY_TMP}")
        set(MYSQL_ADD_INCLUDE_DIR ${MY_TMP} CACHE FILEPATH INTERNAL)

        # set LIBRARY_DIR
        exec_program(${MYSQL_CONFIG}
                     ARGS --libs
                     OUTPUT_VARIABLE MY_TMP)
        set(MYSQL_ADD_LIBRARIES "")
        string(REGEX MATCHALL "(^| )-l[^ ]+" MYSQL_LIB_LIST "${MY_TMP}")
        foreach(LIB ${MYSQL_LIB_LIST})
            string(REGEX REPLACE "[ ]*-l([^ ]*)" "\\1" LIB "${LIB}")
            list(APPEND MYSQL_ADD_LIBRARIES "${LIB}")
        endforeach(LIB ${MYSQL_LIBS})

        # Add mysqlclient library
        set(MYSQL_ADD_LIBRARY_PATH "")
        string(REGEX MATCHALL "-L[^ ]+" MYSQL_LIBDIR_LIST "${MY_TMP}")
        foreach(LIB ${MYSQL_LIBDIR_LIST})
            string(REGEX REPLACE "[ ]*-L([^ ]*)" "\\1" LIB "${LIB}")
            list(APPEND MYSQL_ADD_LIBRARY_PATH "${LIB}")
        endforeach(LIB ${MYSQL_LIBS})

        # Set MYSQL_VERSION
        exec_program(${MYSQL_CONFIG}
                     ARGS --version
                     OUTPUT_VARIABLE MY_TMP)
        set(MySQL_VERSION "")
        set(MySQL_VERSION ${MY_TMP})

    else(MYSQL_CONFIG)
        set(MYSQL_ADD_LIBRARIES "")
        list(APPEND MYSQL_ADD_LIBRARIES "mysqlclient")
    endif(MYSQL_CONFIG)

else(UNIX)
    if (WIN32)
        set(MYSQL_ADD_LIBRARIES "")
        list(APPEND MYSQL_ADD_LIBRARIES "mysql")
    endif (WIN32)
    set(MYSQL_ADD_INCLUDE_DIR "c:/msys/local/include" CACHE FILEPATH INTERNAL)
    set(MYSQL_ADD_LIBRARY_PATH "c:/msys/local/lib" CACHE FILEPATH INTERNAL)
ENDIF(UNIX)

find_path(MySQL_INCLUDE_DIR mysql.h
          /usr/local/include
          /usr/local/include/mysql
          /usr/local/mysql/include
          /usr/local/mysql/include/mysql
          /opt/mysql/mysql/include
          /opt/mysql/mysql/include/mysql
          /usr/include
          /usr/include/mysql
          ${MYSQL_INCLUDEDIR}
)

set(TMP_MYSQL_LIBRARIES "")

foreach(LIB ${MYSQL_ADD_LIBRARIES})
    find_library("MYSQL_LIBRARIES_${LIB}" NAMES ${LIB}
        PATHS
        ${MYSQL_LIBRARYDIR}
        /usr/lib64/mysql
        /usr/lib/mysql
        /usr/local/lib64
        /usr/local/lib
        /usr/local/lib64/mysql
        /usr/local/lib/mysql
        /usr/local/mysql64/lib
        /usr/local/mysql/lib
    )
    list(APPEND TMP_MYSQL_LIBRARIES "${MYSQL_LIBRARIES_${LIB}}")
endforeach(LIB ${MYSQL_ADD_LIBRARIES})

set(MySQL_LIBRARIES ${TMP_MYSQL_LIBRARIES} CACHE FILEPATH INTERNAL)

if(MySQL_VERSION)
        STRING(REGEX REPLACE ".*([456])\\.[0-9]\\..*" "\\1" MySQL_MAJOR_VERSION "${MySQL_VERSION}")
        STRING(REGEX REPLACE ".*[456]\\.([0-9])\\..*" "\\1" MySQL_MINOR_VERSION "${MySQL_VERSION}")
else(MySQL_VERSION)
    if(MySQL_INCLUDE_DIR)
        FILE(READ "${MySQL_INCLUDE_DIR}/mysql_version.h" _MYSQL_VERSION_H_CONTENTS)
        STRING(REGEX REPLACE "^.*#define MYSQL_SERVER_VERSION.*\"([456]\\.[0-9]\\.[0-9]+).*\".*$" "\\1" MySQL_VERSION ${_MYSQL_VERSION_H_CONTENTS})
        STRING(REGEX REPLACE ".*([456])\\.[0-9]\\..*" "\\1" MYSQL_MAJOR_VERSION "${MySQL_VERSION}")
        STRING(REGEX REPLACE ".*[456]\\.([0-9])\\..*" "\\1" MYSQL_MINOR_VERSION "${MySQL_VERSION}")
    endif(MySQL_INCLUDE_DIR)
endif(MySQL_VERSION)

set(MYSQL_DIRECTORIES
    ${MYSQL_LIBRARYDIR}
    /usr/lib64/mysql
    /usr/lib/mysql
    /usr/local/lib64/mysql
    /usr/local/lib/mysql
)
message(STATUS "MySQL Version: ${MySQL_VERSION}")

set ( ${MySQL_PLUGIN_DIR} "")

exec_program(${MYSQL_CONFIG}
     ARGS --plugindir
     OUTPUT_VARIABLE MY_PLUGIN_TEMP)

if (MY_PLUGIN_TEMP)
    set ( MySQL_PLUGIN_DIR ${MY_PLUGIN_TEMP})
else (MY_PLUGIN_TEMP)
    if (${MySQL_VERSION} MATCHES "^5\\.[15]|^6\\.")
      foreach (MYSQL_DIR ${MYSQL_DIRECTORIES})
        if (IS_DIRECTORY "${MYSQL_DIR}/plugin")
          set (MySQL_PLUGIN_DIR "${MYSQL_DIR}/plugin")
        endif (IS_DIRECTORY "${MYSQL_DIR}/plugin")
      endforeach (MYSQL_DIR MYSQL_DIRECTORIES)
    endif (${MySQL_VERSION} MATCHES "^5\\.[15]|^6\\.")
endif (MY_PLUGIN_TEMP)

message(STATUS "MySQL Plugin Dir: ${MySQL_PLUGIN_DIR}")

if(MySQL_INCLUDE_DIR AND MySQL_LIBRARIES)
    set(MySQL_FOUND TRUE CACHE INTERNAL "MySQL found")
    message(STATUS "Found MySQL ${MySQL_VERSION}: ${MySQL_INCLUDE_DIR}, ${MySQL_LIBRARIES}")
else(MySQL_INCLUDE_DIR AND MySQL_LIBRARIES)
    set(MySQL_FOUND FALSE CACHE INTERNAL "MySQL found")
    message(STATUS "MySQL not found.")
endif(MySQL_INCLUDE_DIR AND MySQL_LIBRARIES)
mark_as_advanced(MySQL_INCLUDE_DIR MySQL_LIBRARIES)
