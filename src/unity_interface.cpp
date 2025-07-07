// src/unity_interface.cpp

#include <iostream>
#include <map>
#include <filesystem>
#include "phonemize.hpp"
#include "phoneme_ids.hpp"

extern "C" {
#include <espeak-ng/speak_lib.h>
}

#if defined(_WIN32)
#define EXPORT_API __declspec(dllexport)
#else
#define EXPORT_API __attribute__((visibility("default")))
#endif

extern "C" {

    // Hàm khởi tạo, nhận đường dẫn đến thư mục espeak-ng-data
    EXPORT_API int InitializePhonemizer(const char* espeakDataPath) {
        try {
            int result = espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 0, espeakDataPath, 0);
            if (result < 0) {
                std::cerr << "Failed to initialize eSpeak" << std::endl;
                return -1;
            }
            return 0; // Success
        } catch (const std::exception& e) {
            std::cerr << "Initialization failed: " << e.what() << std::endl;
            return -1; // Failure
        }
    }

    // Hàm chính để phoneme hóa văn bản và trả về mảng các ID
    EXPORT_API void PhonemizeText(
        const char* text,
        const char* voice,
        long long** outPhonemeIds,
        int* outNumPhonemeIds) {

        piper::eSpeakPhonemeConfig config;
        config.voice = std::string(voice);

        std::vector<std::vector<piper::Phoneme>> phonemes;
        piper::phonemize_eSpeak(std::string(text), config, phonemes);

        // Flatten all phonemes from all sentences
        std::vector<piper::Phoneme> flattenedPhonemes;
        for (const auto& sentence : phonemes) {
            for (const auto& phoneme : sentence) {
                flattenedPhonemes.push_back(phoneme);
            }
        }

        // Convert phonemes to IDs
        piper::PhonemeIdConfig idConfig;
        std::vector<piper::PhonemeId> phonemeIds;
        std::map<piper::Phoneme, std::size_t> missingPhonemes;
        piper::phonemes_to_ids(flattenedPhonemes, idConfig, phonemeIds, missingPhonemes);

        *outNumPhonemeIds = phonemeIds.size();
        if (*outNumPhonemeIds > 0) {
            // Cấp phát bộ nhớ cho mảng kết quả
            *outPhonemeIds = new long long[*outNumPhonemeIds];
            for (int i = 0; i < *outNumPhonemeIds; ++i) {
                (*outPhonemeIds)[i] = phonemeIds[i];
            }
        } else {
            *outPhonemeIds = nullptr;
        }
    }

    // Hàm giải phóng bộ nhớ đã được cấp phát
    EXPORT_API void FreePhonemeIds(long long* phonemeIds) {
        if (phonemeIds != nullptr) {
            delete[] phonemeIds;
        }
    }
}