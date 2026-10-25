# ESP-IDF project (target esp32s3). NOT built or run in this repository's CI/host
# environment: ESP-IDF is not installed here, so this HAL is UNTESTED ON TARGET.
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(parkflow_lane_controller)
