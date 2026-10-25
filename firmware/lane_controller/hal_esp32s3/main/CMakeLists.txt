file(GLOB CORE_SRC ${CMAKE_CURRENT_LIST_DIR}/../../src/*.cpp)
idf_component_register(SRCS "app_main.cpp" "hal_esp32s3.cpp" ${CORE_SRC}
                       INCLUDE_DIRS "." "../../include"
                       REQUIRES driver esp_adc esp_timer esp_hw_support freertos)
