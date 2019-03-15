#!/bin/bash

#believe that klee is already installed

way_to_main_fld='/root/governor-mysql-1.2'
way_to_klee_fld='/tests/Klee/'

function prepare_and_run_tests() {
    #to create lscapi_config.h with version
    pushd ${way_to_main_fld}
    cmake .
    make
    popd

    pushd ${way_to_main_fld}${way_to_klee_fld}
    cmake3 -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ .
    make
    ldconfig /usr/local/lib
    #run tests
    ./scripts/run_suites.py
    popd
}

prepare_and_run_tests
