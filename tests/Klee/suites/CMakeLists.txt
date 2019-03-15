MACRO(ADD_MODULE file)
    ADD_EXECUTABLE( ${file}.bc ${file}.c $<TARGET_OBJECTS:objects> )
ENDMACRO(ADD_MODULE file)

FILE(GLOB C_FILES RELATIVE "${CMAKE_SOURCE_DIR}/suites" "${CMAKE_SOURCE_DIR}/suites/*.c")

include_directories("${CMAKE_CURRENT_SOURCE_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}/../../../src" "${CMAKE_CURRENT_SOURCE_DIR}/../")

FOREACH ( module ${C_FILES} )
    STRING( REGEX REPLACE ".c$" "" module "${module}" )
    MESSAGE(STATUS "Found test suite: ${module}")
    ADD_MODULE(${module})
ENDFOREACH ( module ${MODULES} )


