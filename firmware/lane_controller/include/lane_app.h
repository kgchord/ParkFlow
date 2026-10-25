// Glue: HAL <-> pure FSM. One call to tick() is one control cycle.
#pragma once
#include "edge_link.h"
#include "hal.h"
#include "indicators.h"
#include "lane_fsm.h"
#include "rfid_parser.h"
#include "support.h"
namespace pf {

class LaneApp {
 public:
  LaneApp(IHal& hal, const Config& cfg, const RfidFrameCfg& rfid);
  void tick();                          // call every cfg.loop_period_ms
  const LaneFsm& fsm() const { return fsm_; }
  const RfidParser& rfid() const { return rfid_; }
  const EdgeLineParser& edge() const { return edge_; }
  uint32_t wdi_kicks() const { return wdi_kicks_; }
  static constexpr int kTaskControl = 0;
  static constexpr uint32_t kContactorSettleMs = 60;   // placeholder: LC1D09 pull-in time to be measured
 private:
  void send_edge(const char* b, size_t n) { if (n) hal_.edge_write(reinterpret_cast<const uint8_t*>(b), n); }
  IHal& hal_;
  LaneFsm fsm_;
  RfidParser rfid_;
  EdgeLineParser edge_;
  TaskSupervisor sup_;
  Debounce d_beam_, d_pres_, d_up_, d_dn_, d_estop_;
  Outputs out_;
  bool rearm_prev_ = false;
  uint32_t last_status_ = 0, wdi_kicks_ = 0;
  bool k1_on_ = false;
  uint32_t k1_t_ = 0;
  bool first_ = true;
  const char* last_sign_ = nullptr;
  const RfidFrameCfg rcfg_;
};
}  // namespace pf
