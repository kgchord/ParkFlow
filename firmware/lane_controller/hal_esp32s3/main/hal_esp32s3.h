#pragma once
#include "hal.h"
namespace pf {
IHal& esp32s3_hal();   // singleton, initialises GPIO/UART/ADC on first use
}
