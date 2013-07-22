CMAKE_MINIMUM_REQUIRED(VERSION 2.4)

PROJECT(MYSQL_GOVERNOR C)

SET(CMAKE_BUILD_TYPE Debug)
SET(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
FIND_PACKAGE(GLIB2 REQUIRED)
#FIND_PACKAGE(MySQL REQUIRED)

INCLUDE_DIRECTORIES(${GLIB2_INCLUDE_DIRS})
#LINK_LIBRARIES(${GLIB2_LIBRARIES} ${MYSQL_CLIENT_LIBS})
#INCLUDE_DIRECTORIES(${GLIB2_INCLUDE_DIRS})
LINK_LIBRARIES(${GLIB2_LIBRARIES})
LINK_LIBRARIES(pthread)
LINK_LIBRARIES(m)
LINK_LIBRARIES(rt)
LINK_LIBRARIES(dl)
LINK_LIBRARIES(ncurses)

SET(EXECUTABLE_OUTPUT_PATH "${CMAKE_SOURCE_DIR}/bin/")
SET(LIBRARY_OUTPUT_PATH "${CMAKE_SOURCE_DIR}/lib/")

SET(SRC "${CMAKE_SOURCE_DIR}/src/")
SET(config_SRC ${SRC}/governor_config.c ${SRC}/ezxml.c)
SET(db_governor_SRC ${SRC}/governor.c 
                    ${config_SRC} 
                    ${SRC}/fifo_stats.c 
                    ${SRC}/stats.c 
                    ${SRC}/user_account.c 
                    ${SRC}/dbgovernor_string_functions.c 
                    ${SRC}/log.c 
                    ${SRC}/wrappers.c 
                    ${SRC}/dlload.c
                    ${SRC}/calc_stats.c
                    ${SRC}/governor_server.c
                    ${SRC}/governor_write_data.c
                    ${SRC}/parce_proc_fs.c
                    ${SRC}/tick_generator.c 
                    ${SRC}/tid_table.c
                    ${SRC}/mysql_connector_common.c
                    ${SRC}/log-decoder.c
                    ${SRC}/getsysinfo.c
                    ${SRC}/commands.c
                    ${SRC}/dbtop_server.c
                    ${SRC}/shared_memory.c
                    ${SRC}/dbuser_map.c
)
SET(dbtop_SRC ${SRC}/dbtop.c ${SRC}/dbgovernor_string_functions.c ${SRC}/wrappers.c)
SET(governor_lib_src ${SRC}/dbgovernor_string_functions.c 
                    ${SRC}/governor_write_data.c
                    ${SRC}/parce_proc_fs.c
                    ${SRC}/shared_memory.c             
)
SET(mysql_unfreeze_SRC ${SRC}/mysql_unfreeze.c 
						${SRC}/wrappers.c ${SRC}/mysql_connector_common.c 
						${SRC}/dbgovernor_string_functions.c 
						${SRC}/dlload.c 
						${SRC}/log.c 
						${config_SRC}
						${SRC}/shared_memory.c
                    ${SRC}/calc_stats.c
                    ${SRC}/user_account.c 
                    ${SRC}/stats.c 
                    ${SRC}/fifo_stats.c 
                    ${SRC}/tick_generator.c 
                    ${SRC}/tid_table.c
                    ${SRC}/log-decoder.c
                    ${SRC}/getsysinfo.c
                    ${SRC}/commands.c
                    ${SRC}/dbuser_map.c
						)
                    
SET(dbctl_SRC ${SRC}/dbctl.c 
                    ${SRC}/dbctl_set.c 
                    ${SRC}/dbctl_list.c 
                    ${SRC}/dbctl_rest.c
                    ${SRC}/dbctl_conn.c
                    ${SRC}/dbctl_cfg.c
                    
                    ${SRC}/shared_memory.c
                    ${SRC}/log.c
                    ${SRC}/dlload.c
                    ${SRC}/wrappers.c
                    ${SRC}/dbgovernor_string_functions.c 
                    ${SRC}/calc_stats.c
                    ${SRC}/user_account.c 
                    ${SRC}/stats.c 
                    ${SRC}/fifo_stats.c 
                    ${SRC}/tick_generator.c 
                    ${SRC}/tid_table.c
                    ${SRC}/log-decoder.c
                    ${SRC}/getsysinfo.c
                    ${SRC}/commands.c
                    ${SRC}/dbuser_map.c
                    ${SRC}/mysql_connector_common.c
					${config_SRC}
                    )
SET(governor_lib_src ${SRC}/dbgovernor_string_functions.c 
                    ${SRC}/governor_write_data.c
                    ${SRC}/parce_proc_fs.c
                    ${SRC}/shared_memory.c             
)
SET_SOURCE_FILES_PROPERTIES(${db_governor_SRC} ${dbtop_SRC} ${governor_lib_src} ${mysql_unfreeze_SRC} ${dbctl_SRC} PROPERTIES COMPILE_FLAGS "-DOK -g")

ADD_EXECUTABLE(db_governor ${db_governor_SRC})
ADD_EXECUTABLE(dbtop ${dbtop_SRC})
ADD_EXECUTABLE(mysql_unfreeze ${mysql_unfreeze_SRC})
ADD_LIBRARY(governor SHARED ${governor_lib_src})
ADD_EXECUTABLE(dbctl ${dbctl_SRC})

INSTALL(TARGETS db_governor dbtop mysql_unfreeze dbctl
  DESTINATION bin
  COMPONENT Runtime)
  
INSTALL(TARGETS governor
        DESTINATION lib
        PERMISSIONS OWNER_READ GROUP_READ WORLD_READ)




