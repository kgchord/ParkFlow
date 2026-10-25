// Tiny test harness: no dependencies.  TEST(name){ CHECK(cond); CHECK_EQ(a,b); }
#pragma once
#include <cstdio>
#include <cstdlib>
#include <vector>
namespace mt {
struct Case { const char* name; void (*fn)(); };
inline std::vector<Case>& registry() { static std::vector<Case> r; return r; }
inline int& checks() { static int c = 0; return c; }
inline int& failures() { static int f = 0; return f; }
inline const char*& current() { static const char* c = ""; return c; }
struct Reg { Reg(const char* n, void (*f)()) { registry().push_back({n, f}); } };
inline int run_all() {
  int failed_cases = 0;
  for (auto& c : registry()) {
    int before = failures();
    current() = c.name;
    c.fn();
    bool ok = failures() == before;
    std::printf("[%s] %s\n", ok ? " OK " : "FAIL", c.name);
    if (!ok) ++failed_cases;
  }
  std::printf("\n%zu tests, %d checks, %d failed checks, %d failed tests\n", registry().size(), checks(), failures(), failed_cases);
  return failed_cases ? 1 : 0;
}
}  // namespace mt
#define TEST(name) static void name(); static mt::Reg reg_##name(#name, name); static void name()
#define CHECK(c) do { ++mt::checks(); if (!(c)) { ++mt::failures(); std::printf("  CHECK FAILED %s:%d in %s: %s\n", __FILE__, __LINE__, mt::current(), #c); } } while (0)
#define CHECK_EQ(a, b) do { ++mt::checks(); long long _a = (long long)(a), _b = (long long)(b); if (_a != _b) { ++mt::failures(); std::printf("  CHECK_EQ FAILED %s:%d in %s: %s (=%lld) != %s (=%lld)\n", __FILE__, __LINE__, mt::current(), #a, _a, #b, _b); } } while (0)
