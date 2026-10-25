# Host build + unit tests. No network, no ESP-IDF needed.
CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O1 -g -Wall -Wextra -Wpedantic -Werror -Iinclude -Itest
SRC      := $(wildcard src/*.cpp)
TESTS    := $(wildcard test/*.cpp)
BUILD    := build

all: $(BUILD)/test_all $(BUILD)/test_all_san

$(BUILD)/test_all: $(SRC) $(TESTS) $(wildcard include/*.h test/*.h)
	@mkdir -p $(BUILD)
	$(CXX) $(CXXFLAGS) $(SRC) $(TESTS) -o $@

$(BUILD)/test_all_san: $(SRC) $(TESTS) $(wildcard include/*.h test/*.h)
	@mkdir -p $(BUILD)
	$(CXX) $(CXXFLAGS) -fsanitize=address,undefined -fno-sanitize-recover=undefined $(SRC) $(TESTS) -o $@

test: $(BUILD)/test_all $(BUILD)/test_all_san
	./$(BUILD)/test_all
	./$(BUILD)/test_all_san

clean:
	rm -rf $(BUILD)
.PHONY: all test clean
