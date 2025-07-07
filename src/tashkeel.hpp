#ifndef TASHKEEL_H_
#define TASHKEEL_H_

#include <map>
#include <set>
#include <string>

#ifndef NO_ONNXRUNTIME
#include <onnxruntime_cxx_api.h>
#endif

#include "shared.hpp"

// https://github.com/mush42/libtashkeel
namespace tashkeel {

const std::string instanceName = "piper_tashkeel";
const int PAD_ID = 0;
const int UNK_ID = 1;
const std::size_t MAX_INPUT_CHARS = 315;

extern std::set<char32_t> HARAKAT_CHARS;
extern std::set<int> INVALID_HARAKA_IDS;
extern std::map<char32_t, int> inputVocab;
extern std::map<int, std::vector<char32_t>> outputVocab;

#ifndef NO_ONNXRUNTIME
struct State {
  Ort::Session onnx;
  Ort::AllocatorWithDefaultOptions allocator;
  Ort::SessionOptions options;
  Ort::Env env;

  State() : onnx(nullptr){};
};
#else
struct State {
  // Placeholder for when onnxruntime is not available
  int placeholder;
  
  State() : placeholder(0){};
};
#endif

PIPERPHONEMIZE_EXPORT void tashkeel_load(std::string modelPath, State &state);
PIPERPHONEMIZE_EXPORT std::string tashkeel_run(std::string text, State &state);

} // namespace tashkeel

#endif // TASHKEEL_H_
