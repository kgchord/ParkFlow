// UNTESTED ON TARGET. One high-priority control task at 2 ms; everything safety-relevant
// lives in LaneApp/LaneFsm (host-tested).
#include "esp_task_wdt.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "hal_esp32s3.h"
#include "lane_app.h"

static void control_task(void*) {
  static pf::LaneApp app(pf::esp32s3_hal(), pf::Config(), pf::kIllustrativeProfile);   // TODO: real reader profile
  esp_task_wdt_add(nullptr);
  TickType_t last = xTaskGetTickCount();
  for (;;) {
    app.tick();
    vTaskDelayUntil(&last, pdMS_TO_TICKS(2));
  }
}

extern "C" void app_main(void) {
  xTaskCreatePinnedToCore(control_task, "control", 6144, nullptr, configMAX_PRIORITIES - 2, nullptr, 1);
}
