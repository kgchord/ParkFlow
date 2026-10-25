#include <cstdio>
#include <cstring>
#include <set>
#include <string>
#include "edge_link.h"
#include "indicators.h"
#include "minitest.h"
#include "pins.h"
#include "rfid_parser.h"
#include "support.h"
using namespace pf;

// ---------------------------------------------------------------- CRC
TEST(crc_known_check_values_123456789) {
  const uint8_t d[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  CHECK_EQ(crc_compute(CrcType::CRC16_CCITT_FALSE, d, 9), 0x29B1);
  CHECK_EQ(crc_compute(CrcType::CRC16_ARC, d, 9), 0xBB3D);
  CHECK_EQ(crc_compute(CrcType::CRC16_MODBUS, d, 9), 0x4B37);
  CHECK_EQ(crc_compute(CrcType::XOR8, d, 9), 0x31);
  CHECK_EQ(crc_compute(CrcType::SUM8, d, 9), (0x31 + 0x32 + 0x33 + 0x34 + 0x35 + 0x36 + 0x37 + 0x38 + 0x39) & 0xFF);
}

// ---------------------------------------------------------------- RFID parser
static const uint8_t EPC_A[12] = {0xE2, 0x80, 0x11, 0x60, 0x60, 0x00, 0x02, 0x05, 0x5A, 0x11, 0x22, 0x33};

TEST(rfid_parses_good_frame_with_signed_rssi) {
  RfidParser p(kIllustrativeProfile);
  uint8_t f[64]; size_t n = illustrative_encode(f, sizeof f, EPC_A, 12, -47);
  CHECK_EQ(n, 6 + 12 + 2);
  for (size_t i = 0; i < n; ++i) p.push(f[i]);
  TagFrame t;
  CHECK(p.pop(t));
  CHECK_EQ(t.epc_len, 12);
  CHECK(std::memcmp(t.epc, EPC_A, 12) == 0);
  CHECK(t.has_rssi && t.rssi == -47);
  CHECK(!p.pop(t));
  CHECK_EQ(p.stats().frames_ok, 1);
}

TEST(rfid_resyncs_after_noise_split_and_back_to_back_frames) {
  RfidParser p(kIllustrativeProfile);
  uint8_t f1[64], f2[64];
  size_t n1 = illustrative_encode(f1, sizeof f1, EPC_A, 12, -40);
  size_t n2 = illustrative_encode(f2, sizeof f2, EPC_A, 8, -70);
  const uint8_t noise[] = {0x00, 0xA5, 0x13, 0xFF, 0xA5, 0xA5, 0x5A, 0x02};   // includes false SOF starts
  for (uint8_t b : noise) p.push(b);
  for (size_t i = 0; i < n1; ++i) p.push(f1[i]);
  for (size_t i = 0; i < n2; ++i) p.push(f2[i]);
  TagFrame t;
  CHECK(p.pop(t)); CHECK_EQ(t.epc_len, 12); CHECK_EQ(t.rssi, -40);
  CHECK(p.pop(t)); CHECK_EQ(t.epc_len, 8); CHECK_EQ(t.rssi, -70);
  CHECK(!p.pop(t));
}

TEST(rfid_bad_crc_is_dropped_and_next_frame_still_decodes) {
  RfidParser p(kIllustrativeProfile);
  uint8_t f1[64], f2[64];
  size_t n1 = illustrative_encode(f1, sizeof f1, EPC_A, 12, -40);
  size_t n2 = illustrative_encode(f2, sizeof f2, EPC_A, 12, -41);
  f1[8] ^= 0x01;                       // corrupt one EPC bit
  for (size_t i = 0; i < n1; ++i) p.push(f1[i]);
  for (size_t i = 0; i < n2; ++i) p.push(f2[i]);
  TagFrame t;
  CHECK(p.pop(t)); CHECK_EQ(t.rssi, -41);
  CHECK(!p.pop(t));
  CHECK(p.stats().bad_crc >= 1);
}

TEST(rfid_rejects_absurd_length_and_non_tag_type) {
  RfidParser p(kIllustrativeProfile);
  const uint8_t bad_len[] = {0xA5, 0x5A, 0xFF, 0x01, 0x00};
  for (uint8_t b : bad_len) p.push(b);
  CHECK(p.stats().bad_len >= 1);
  uint8_t f[64]; size_t n = illustrative_encode(f, sizeof f, EPC_A, 12, -40);
  f[3] = 0x02;                          // different frame type
  uint16_t c = crc_compute(CrcType::CRC16_CCITT_FALSE, f + 2, n - 4);
  f[n - 2] = c >> 8; f[n - 1] = c & 0xFF;
  for (size_t i = 0; i < n; ++i) p.push(f[i]);
  TagFrame t;
  CHECK(!p.pop(t));
  CHECK_EQ(p.stats().other, 1);
}

TEST(rfid_parser_is_configurable_for_a_different_layout) {
  // Different invented layout: no SOF, len byte first (=payload+1), type, 12-byte fixed EPC,
  // unsigned RSSI, CRC16-ARC little-endian over everything before it.
  RfidFrameCfg c;
  c.sof_len = 0; c.len_offset = 0; c.len_adjust = 3;       // total = len + 3 (len, then payload, then 2 CRC)
  c.min_total = 6; c.max_total = 40;
  c.crc = CrcType::CRC16_ARC; c.crc_big_endian = false; c.crc_start = 0;
  c.filter_type = true; c.type_offset = 1; c.type_tag_notify = 0x90;
  c.epc_len_offset = 0xFF; c.epc_len_fixed = 12; c.epc_offset = 2;
  c.rssi_offset = 14; c.rssi_signed = false;
  uint8_t f[20]; f[0] = 1 + 12 + 1; f[1] = 0x90; std::memcpy(f + 2, EPC_A, 12); f[14] = 200;
  uint16_t crc = crc_compute(CrcType::CRC16_ARC, f, 15);
  f[15] = crc & 0xFF; f[16] = crc >> 8;
  CHECK_EQ(f[0] + 3, 17);
  RfidParser p(c);
  for (int i = 0; i < 17; ++i) p.push(f[i]);
  TagFrame t;
  CHECK(p.pop(t));
  CHECK(std::memcmp(t.epc, EPC_A, 12) == 0);
  CHECK_EQ(t.rssi, 200);
}

// ---------------------------------------------------------------- edge link
static std::string mkline(const std::string& body) {
  uint8_t ck = 0; for (char ch : body) ck ^= (uint8_t)ch;
  char tail[8]; std::snprintf(tail, sizeof tail, "*%02X\n", ck);
  return "$" + body + tail;
}
static bool feed(EdgeLineParser& p, const std::string& s, EdgeMsg& m) {
  bool got = false;
  for (char ch : s) if (p.push((uint8_t)ch, m)) got = true;
  return got;
}

TEST(edge_decodes_all_command_types) {
  EdgeLineParser p; EdgeMsg m;
  CHECK(feed(p, mkline("HB,42"), m)); CHECK(m.type == EdgeMsgType::HB); CHECK_EQ(m.n, 42);
  CHECK(feed(p, mkline("DEC,17,G,3"), m)); CHECK(m.type == EdgeMsgType::DEC); CHECK_EQ(m.n, 17);
  CHECK(m.decision == Decision::GRANT); CHECK_EQ(m.reason, 3);
  CHECK(feed(p, mkline("DEC,18,F,1"), m)); CHECK(m.decision == Decision::FALLBACK);
  CHECK(feed(p, mkline("DEC,19,D,2"), m)); CHECK(m.decision == Decision::DENY);
  CHECK(feed(p, mkline("GUARD"), m)); CHECK(m.type == EdgeMsgType::GUARD);
  CHECK(feed(p, mkline("REARM"), m)); CHECK(m.type == EdgeMsgType::REARM);
  CHECK(feed(p, mkline("RESET"), m)); CHECK(m.type == EdgeMsgType::RESET);
}

TEST(edge_known_vector_shared_with_python_tests) {
  EdgeLineParser p; EdgeMsg m;
  CHECK(feed(p, "$HB,1*17\n", m));                       // same literal asserted in edge_node/tests/test_node_and_sim.py
  CHECK(m.type == EdgeMsgType::HB && m.n == 1);
}

TEST(edge_rejects_bad_checksum_garbage_and_unknown) {
  EdgeLineParser p; EdgeMsg m;
  std::string l = mkline("DEC,17,G,0"); l[l.size() - 3] = (l[l.size() - 3] == '0') ? '1' : '0';
  CHECK(!feed(p, l, m));
  CHECK_EQ(p.bad_checksum(), 1);
  CHECK(!feed(p, "garbage\n$$$\n$HB,1\n", m));          // no checksum
  CHECK(!feed(p, mkline("NOPE,1"), m));
  CHECK(!feed(p, mkline("DEC,1,X,0"), m));
  std::string longl = "$HB,"; longl.append(300, '9'); longl += "\n";
  CHECK(!feed(p, longl, m));
  CHECK(feed(p, mkline("HB,2"), m));                     // parser recovered
}

TEST(edge_encode_events_roundtrip_checksum) {
  char b[128]; TxEvent e;
  e.type = TxType::TAG; e.seq = 9; e.peak_ms = 1234; e.n_distinct = 2;
  e.tag.epc_len = 4; e.tag.epc[0] = 0xDE; e.tag.epc[1] = 0xAD; e.tag.epc[2] = 0xBE; e.tag.epc[3] = 0xEF;
  e.tag.has_rssi = true; e.tag.rssi = -52;
  size_t n = encode_tx_event(b, sizeof b, e);
  CHECK(n > 0);
  std::string s(b, n);
  CHECK(s.rfind("$TAG,9,DEADBEEF,-52,1234,2*", 0) == 0);
  CHECK(s.back() == '\n');
  uint8_t ck = 0; for (size_t i = 1; i < s.size() - 4; ++i) ck ^= (uint8_t)s[i];
  char hex[3]; std::snprintf(hex, 3, "%02X", ck);
  CHECK(s.substr(s.size() - 3, 2) == hex);
  e = TxEvent(); e.type = TxType::NOTAG; e.seq = 3;
  n = encode_tx_event(b, sizeof b, e); CHECK(std::string(b, n).rfind("$NOTAG,3*", 0) == 0);
  CHECK_EQ(encode_tx_event(b, 5, e), 0);                 // too small buffer
  n = encode_status(b, sizeof b, State::IDLE, Fault::NONE, 3, 24000);
  CHECK(std::string(b, n).rfind("$ST,IDLE,NONE,3,24000*", 0) == 0);
}

// ---------------------------------------------------------------- indicators
TEST(buzzer_and_led_patterns) {
  CHECK(buzzer_level(Buzz::BEEP_SHORT_1S, 50) && !buzzer_level(Buzz::BEEP_SHORT_1S, 500));
  CHECK(buzzer_level(Buzz::DOUBLE_BEEP_3S, 50) && !buzzer_level(Buzz::DOUBLE_BEEP_3S, 200) && buzzer_level(Buzz::DOUBLE_BEEP_3S, 300) && !buzzer_level(Buzz::DOUBLE_BEEP_3S, 1000));
  CHECK(buzzer_level(Buzz::SLOW_PULSE_5S, 500) && !buzzer_level(Buzz::SLOW_PULSE_5S, 2000));
  CHECK(!buzzer_level(Buzz::OFF, 0));
  // fault code N: count rising edges in one cycle
  for (uint8_t n = 1; n <= 5; ++n) {
    int edges = 0; bool prev = false;
    for (uint32_t t = 0; t < (uint32_t)n * 400u + 1200u; ++t) { bool l = led_lit(LedMode::FAULT_CODE, n, t); if (l && !prev) ++edges; prev = l; }
    CHECK_EQ(edges, n);
  }
  CHECK(led_lit(LedMode::SOLID, 0, 12345));
  CHECK(led_lit(LedMode::BLINK_SLOW, 0, 100) && !led_lit(LedMode::BLINK_SLOW, 0, 700));
  CHECK(std::strcmp(sign_text(Sign::SEE_GUARD), "SEE GUARD") == 0);
  CHECK(led_rgb(LedColor::RED).r > 0 && led_rgb(LedColor::RED).g == 0);
}

// ---------------------------------------------------------------- support
TEST(debounce_is_asymmetric) {
  Debounce beam(true, 30, 0);            // clear needs 30 ms, break is instant
  CHECK(beam.update(false, 100) == false);
  CHECK(beam.update(true, 110) == false);
  CHECK(beam.update(true, 125) == false);
  CHECK(beam.update(true, 141) == true);
  CHECK(beam.update(false, 142) == false);
  Debounce pres(false, 0, 30);
  CHECK(pres.update(true, 0) == true);
  CHECK(pres.update(false, 10) == true);
  CHECK(pres.update(true, 20) == true);   // glitch resets the vacant timer
  CHECK(pres.update(false, 30) == true);
  CHECK(pres.update(false, 61) == false);
}

TEST(task_supervisor_flags_a_missed_deadline) {
  TaskSupervisor s; s.configure(0, 50); s.configure(1, 200);
  s.checkin(0, 1000); s.checkin(1, 1000);
  CHECK(s.healthy(1040));
  CHECK(!s.healthy(1060));
  s.checkin(0, 1060);
  CHECK(s.healthy(1100));
  CHECK(!s.healthy(1250));
}

TEST(pin_table_has_no_duplicates_and_matches_schematic_spot_checks) {
  using namespace pf::pins;
  const int all[] = {BOOT_BTN, MOT_ISENSE, BAT_OK, V24_SENSE, MOT_IN_A, MOT_IN_B, MOT_EN, ESTOP_OK, LIM_UP_OK, LIM_DN_OK,
                     BEAM_CLEAR, PRESENCE, AC_OK, WDT_WDI, RS485_DI, RS485_RO, RS485_DE, BUZ_CTRL, USB_DN, USB_DP, WS2812,
                     HUB_A, HUB_B, HUB_CLK, HUB_LAT, HUB_OE, HUB_R, K1_EN, EDGE_TX, EDGE_RX};
  std::set<int> u(all, all + sizeof all / sizeof all[0]);
  CHECK_EQ(u.size(), sizeof all / sizeof all[0]);
  for (int p : all) CHECK(p >= 0 && p <= 48 && p != 22 && p != 23 && p != 24 && p != 25);   // 22-25 do not exist on S3
  for (int p : all) CHECK(!(p >= 26 && p <= 32) && !(p >= 33 && p <= 37));                 // flash/PSRAM pins unused
  CHECK_EQ(MOT_IN_B, 6); CHECK_EQ(ESTOP_OK, 8); CHECK_EQ(K1_EN, 48); CHECK_EQ(EDGE_TX, 43);
}
