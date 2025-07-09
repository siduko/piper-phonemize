cmake_minimum_required(VERSION 3.14)

# Set CMake policies
if(POLICY CMP0114)
    cmake_policy(SET CMP0114 NEW)
endif()

if(POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()

set(CMAKE_VERBOSE_MAKEFILE off)

project(
    piper_phonemize
    VERSION 1.2.0
    DESCRIPTION "Phonemization library for Piper text to speech system"
    HOMEPAGE_URL "https://github.com/rhasspy/piper-phonemize"
    LANGUAGES CXX
)

if(MSVC)
    # Force compiler to use UTF-8 for IPA constants
    add_compile_options("$<$<C_COMPILER_ID:MSVC>:/utf-8>")
    add_compile_options("$<$<CXX_COMPILER_ID:MSVC>:/utf-8>")
elseif(ANDROID)
    # Android flags
    string(APPEND CMAKE_CXX_FLAGS " -Wall -Wextra -fPIC")
    string(APPEND CMAKE_C_FLAGS " -Wall -Wextra -fPIC")
elseif(NOT APPLE)
    # Linux flags
    string(APPEND CMAKE_CXX_FLAGS " -Wall -Wextra -Wl,-rpath,'$ORIGIN'")
    string(APPEND CMAKE_C_FLAGS " -Wall -Wextra")
endif()

add_library(
    piper_phonemize SHARED
    src/phonemize.cpp
    src/phoneme_ids.cpp
    src/tashkeel.cpp
    src/shared.cpp
    src/unity_interface.cpp
)

set_target_properties(piper_phonemize PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)

# ---- onnxruntime ---

# Look for onnxruntime files in <root>/lib
if(NOT DEFINED ONNXRUNTIME_DIR)
    if(NOT DEFINED ONNXRUNTIME_VERSION)
        set(ONNXRUNTIME_VERSION "1.14.1")
    endif()

    if(WIN32)
        # Windows x86-64
        set(ONNXRUNTIME_PREFIX "onnxruntime-win-x64-${ONNXRUNTIME_VERSION}")
        set(ONNXRUNTIME_EXT "zip")
    elseif (APPLE)
        # For iOS builds, onnxruntime is not typically used, so we'll skip it
        if(CMAKE_SYSTEM_NAME STREQUAL "iOS")
            # iOS builds - skip onnxruntime for now
            set(ONNXRUNTIME_PREFIX "")
            set(ONNXRUNTIME_EXT "")
            set(SKIP_ONNXRUNTIME TRUE)
        else()
            # macOS builds
            # Check CMAKE_OSX_ARCHITECTURES first (set by build system), then fall back to CMAKE_SYSTEM_PROCESSOR
            if(CMAKE_OSX_ARCHITECTURES STREQUAL "x86_64" OR CMAKE_SYSTEM_PROCESSOR STREQUAL x86_64)
                # MacOS x86-64
                set(ONNXRUNTIME_PREFIX "onnxruntime-osx-x86_64-${ONNXRUNTIME_VERSION}")
            elseif(CMAKE_OSX_ARCHITECTURES STREQUAL "arm64" OR CMAKE_SYSTEM_PROCESSOR STREQUAL arm64)
                # MacOS Apple Silicon
                set(ONNXRUNTIME_PREFIX "onnxruntime-osx-arm64-${ONNXRUNTIME_VERSION}")
            else()
                message(FATAL_ERROR "Unsupported architecture for onnxruntime: CMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}, CMAKE_SYSTEM_PROCESSOR=${CMAKE_SYSTEM_PROCESSOR}")
            endif()
            
            set(ONNXRUNTIME_EXT "tgz")
        endif()
    else()
        if(ANDROID)
            # Android builds - skip onnxruntime for now as it's complex to set up
            set(SKIP_ONNXRUNTIME TRUE)
            message(STATUS "Skipping onnxruntime for Android build")
        elseif(CMAKE_SYSTEM_PROCESSOR STREQUAL x86_64)
            # Linux x86-64
            set(ONNXRUNTIME_PREFIX "onnxruntime-linux-x64-${ONNXRUNTIME_VERSION}")
        elseif(CMAKE_SYSTEM_PROCESSOR STREQUAL aarch64)
            # Linux ARM 64-bit
            set(ONNXRUNTIME_PREFIX "onnxruntime-linux-aarch64-${ONNXRUNTIME_VERSION}")
        elseif(CMAKE_SYSTEM_PROCESSOR STREQUAL armv7l)
            # Linux ARM 32-bit
            set(ONNXRUNTIME_PREFIX "onnxruntime-linux-arm32-${ONNXRUNTIME_VERSION}")
            set(ONNXRUNTIME_URL "https://github.com/synesthesiam/prebuilt-apps/releases/download/v1.0/onnxruntime-linux-arm32-${ONNXRUNTIME_VERSION}.tgz")
        else()
            message(FATAL_ERROR "Unsupported architecture for onnxruntime")
        endif()

        set(ONNXRUNTIME_EXT "tgz")
    endif()

    if(NOT DEFINED ONNXRUNTIME_URL AND NOT SKIP_ONNXRUNTIME)
        set(ONNXRUNTIME_URL "https://github.com/microsoft/onnxruntime/releases/download/v${ONNXRUNTIME_VERSION}/${ONNXRUNTIME_PREFIX}.${ONNXRUNTIME_EXT}")
    endif()

    if(NOT SKIP_ONNXRUNTIME)
        set(ONNXRUNTIME_FILENAME "${ONNXRUNTIME_PREFIX}.${ONNXRUNTIME_EXT}")
        set(ONNXRUNTIME_DIR "${CMAKE_CURRENT_LIST_DIR}/lib/${ONNXRUNTIME_PREFIX}")

        if(NOT EXISTS "${ONNXRUNTIME_DIR}")
            if(NOT EXISTS "download/${ONNXRUNTIME_FILENAME}")
                # Download onnxruntime release
                message("Downloading ${ONNXRUNTIME_URL}")
                file(DOWNLOAD "${ONNXRUNTIME_URL}" "download/${ONNXRUNTIME_FILENAME}")
            endif()

            # Extract .zip or .tgz to a directory like lib/onnxruntime-linux-x64-1.14.1/
            file(ARCHIVE_EXTRACT INPUT "download/${ONNXRUNTIME_FILENAME}" DESTINATION "${CMAKE_CURRENT_LIST_DIR}/lib")
        endif()
    endif()
endif()

# ---- espeak-ng ---

if(NOT DEFINED ESPEAK_NG_DIR)
    set(ESPEAK_NG_DIR "${CMAKE_CURRENT_BINARY_DIR}/ei")

    include(ExternalProject)
    
    # Prepare CMAKE_ARGS for cross-compilation
    set(ESPEAK_NG_CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX:PATH=${ESPEAK_NG_DIR}
        -DUSE_ASYNC:BOOL=OFF
        -DBUILD_SHARED_LIBS:BOOL=ON
        -DUSE_MBROLA:BOOL=OFF
        -DUSE_LIBSONIC:BOOL=OFF
        -DUSE_LIBPCAUDIO:BOOL=OFF
        -DUSE_KLATT:BOOL=OFF
        -DUSE_SPEECHPLAYER:BOOL=OFF
        -DEXTRA_cmn:BOOL=ON
        -DEXTRA_ru:BOOL=ON
        -DCMAKE_C_FLAGS="-D_FILE_OFFSET_BITS=64"
    )
    
    # Add cross-compilation settings if applicable
    if(CMAKE_TOOLCHAIN_FILE)
        list(APPEND ESPEAK_NG_CMAKE_ARGS -DCMAKE_TOOLCHAIN_FILE=${CMAKE_TOOLCHAIN_FILE})
    endif()
    
    # Propagate system-specific variables
    if(CMAKE_SYSTEM_NAME)
        list(APPEND ESPEAK_NG_CMAKE_ARGS -DCMAKE_SYSTEM_NAME=${CMAKE_SYSTEM_NAME})
    endif()
    
    if(CMAKE_SYSTEM_PROCESSOR)
        list(APPEND ESPEAK_NG_CMAKE_ARGS -DCMAKE_SYSTEM_PROCESSOR=${CMAKE_SYSTEM_PROCESSOR})
    endif()
    
    if(CMAKE_C_COMPILER)
        list(APPEND ESPEAK_NG_CMAKE_ARGS -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER})
    endif()
    
    if(CMAKE_CXX_COMPILER)
        list(APPEND ESPEAK_NG_CMAKE_ARGS -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER})
    endif()
    
    if(ANDROID)
        message(STATUS "Configuring espeak-ng for Android:")
        message(STATUS "  ANDROID_ABI: ${ANDROID_ABI}")
        message(STATUS "  ANDROID_PLATFORM: ${ANDROID_PLATFORM}")
        message(STATUS "  CMAKE_ANDROID_NDK: ${CMAKE_ANDROID_NDK}")
        message(STATUS "  CMAKE_C_COMPILER: ${CMAKE_C_COMPILER}")
        message(STATUS "  CMAKE_CXX_COMPILER: ${CMAKE_CXX_COMPILER}")
        
        list(APPEND ESPEAK_NG_CMAKE_ARGS 
            -DANDROID_ABI=${ANDROID_ABI}
            -DANDROID_PLATFORM=${ANDROID_PLATFORM}
            -DCMAKE_ANDROID_NDK=${CMAKE_ANDROID_NDK}
            -DCMAKE_BUILD_TYPE=Release
            -DCMAKE_POSITION_INDEPENDENT_CODE=ON
            -DBUILD_ESPEAK_NG_EXE=OFF
            -DUSE_ASYNC=OFF
            -DUSE_MBROLA=OFF
            -DUSE_LIBSONIC=OFF
            -DUSE_LIBPCAUDIO=OFF
            -DUSE_KLATT=OFF
            -DUSE_SPEECHPLAYER=OFF
            -DEXTRA_cmn=OFF
            -DEXTRA_ru=OFF
            -DBUILD_ESPEAK_NG_TESTS=OFF
            -DCOMPILE_INTONATIONS=OFF
            -DCOMPILE_MBROLA_VOICES=OFF
            -DCOMPILE_DICTIONARIES=OFF
            -DCOMPILE_PHONEMES=OFF
            -DUSE_MBROLA_VOICES=OFF
            -DBUILD_SHARED_LIBS=OFF
        )
    endif()
    
    if(APPLE)
        # For all Apple platforms (macOS and iOS), ensure architecture is passed
        if(CMAKE_OSX_ARCHITECTURES)
            list(APPEND ESPEAK_NG_CMAKE_ARGS -DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES})
        endif()
        
        if(CMAKE_OSX_DEPLOYMENT_TARGET)
            list(APPEND ESPEAK_NG_CMAKE_ARGS -DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET})
        endif()
        
        # iOS-specific settings
        if(CMAKE_SYSTEM_NAME STREQUAL "iOS")
            list(APPEND ESPEAK_NG_CMAKE_ARGS 
                -DBUILD_ESPEAK_NG_EXE=OFF
                -DBUILD_ESPEAK_NG_TESTS=OFF
                -DBUILD_SHARED_LIBS=OFF
                -DEXTRA_cmn=OFF
                -DEXTRA_ru=OFF
                -DCMAKE_INSTALL_BINDIR=bin
                -DCMAKE_SKIP_BUILD_RPATH=ON
                -DCMAKE_SKIP_INSTALL_RPATH=ON
                # Additional iOS settings to prevent executable builds
                -DENABLE_ASYNC=OFF
                -DENABLE_MBROLA=OFF
                -DENABLE_SONIC=OFF
                -DENABLE_PCAUDIO=OFF
                -DENABLE_KLATT=OFF
                -DENABLE_SPEECHPLAYER=OFF
                -DUSE_ASYNC=OFF
                -DUSE_MBROLA=OFF
                -DUSE_LIBSONIC=OFF
                -DUSE_LIBPCAUDIO=OFF
                -DUSE_KLATT=OFF
                -DUSE_SPEECHPLAYER=OFF
                -DCOMPILE_INTONATIONS=OFF
                -DCOMPILE_MBROLA_VOICES=OFF
                -DCOMPILE_DICTIONARIES=OFF
                -DCOMPILE_PHONEMES=OFF
                -DUSE_MBROLA_VOICES=OFF
                # Force library-only build
                -DBUILD_EXECUTABLES=OFF
                -DBUILD_PROGRAMS=OFF
                -DBUILD_TOOLS=OFF
                -DENABLE_EXECUTABLE=OFF
            )
        endif()
    endif()
    
    # Set up platform-specific patch command for cross-compilation
    if(CMAKE_SYSTEM_NAME STREQUAL "iOS")
        # For iOS, we need to completely disable the espeak-ng-bin executable
        set(ESPEAK_NG_PATCH_COMMAND 
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/espeak-ng-bin/d" {} +
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/TARGET_FILE:espeak-ng-bin/d" {} +
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/MACOSX_BUNDLE/d" {} +
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/add_executable.*espeak-ng-bin/,+10d" {} +
        )
    elseif(ANDROID)
        set(ESPEAK_NG_PATCH_COMMAND 
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/espeak-ng-bin/d" {} +
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/TARGET_FILE:espeak-ng-bin/d" {} +
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/add_executable.*espeak-ng-bin/,+10d" {} +
            # Android-specific patches
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/add_subdirectory.*data/d" {} +
            COMMAND find . -name "CMakeLists.txt" -exec sed -i.bak "/add_dependencies.*data/d" {} +
        )
    else()
        set(ESPEAK_NG_PATCH_COMMAND "")
    endif()
    
    ExternalProject_Add(
        espeak_ng_external
        PREFIX "${CMAKE_CURRENT_BINARY_DIR}/e"
        URL "https://github.com/rhasspy/espeak-ng/archive/0f65aa301e0d6bae5e172cc74197d32a6182200f.zip"
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
        PATCH_COMMAND ${ESPEAK_NG_PATCH_COMMAND}
        CMAKE_ARGS ${ESPEAK_NG_CMAKE_ARGS}
    )
    add_dependencies(piper_phonemize espeak_ng_external)
endif()


# ---- Declare library ----

target_include_directories(
    piper_phonemize PUBLIC
    "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/src>"
    ${ESPEAK_NG_DIR}/include
)

target_link_directories(
    piper_phonemize PUBLIC
    ${ESPEAK_NG_DIR}/lib
)

# Add onnxruntime includes and links only if not skipped
if(NOT SKIP_ONNXRUNTIME)
    target_include_directories(
        piper_phonemize PUBLIC
        ${ONNXRUNTIME_DIR}/include
    )
    target_link_directories(
        piper_phonemize PUBLIC
        ${ONNXRUNTIME_DIR}/lib
    )
    target_link_libraries(
        piper_phonemize
        espeak-ng
        onnxruntime
    )
else()
    # For iOS builds, disable onnxruntime functionality
    target_compile_definitions(piper_phonemize PRIVATE NO_ONNXRUNTIME)
    target_link_libraries(
        piper_phonemize
        espeak-ng
    )
endif()

target_compile_features(piper_phonemize PUBLIC cxx_std_17)

# ---- Declare executable ----

if(NOT ANDROID AND NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
    add_executable(piper_phonemize_exe src/main.cpp src/phoneme_ids.cpp)

    if(NOT WIN32)
        set_property(TARGET piper_phonemize_exe PROPERTY OUTPUT_NAME piper_phonemize)
    endif()

    target_compile_features(piper_phonemize_exe PUBLIC cxx_std_17)

    target_include_directories(
        piper_phonemize_exe PUBLIC
        "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/src>"
        ${ESPEAK_NG_DIR}/include
    )

    target_link_directories(
        piper_phonemize_exe PUBLIC
        ${ESPEAK_NG_DIR}/lib
    )

    target_link_libraries(piper_phonemize_exe PUBLIC
        piper_phonemize
        espeak-ng
    )
endif()

# ---- Declare test ----

if(NOT ANDROID AND NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
    include(CTest)
    enable_testing()
    add_executable(test_piper_phonemize src/test.cpp src/phoneme_ids.cpp)
    add_test(
        NAME test_piper_phonemize
        COMMAND test_piper_phonemize "${ESPEAK_NG_DIR}/share/espeak-ng-data" "${CMAKE_SOURCE_DIR}/etc/libtashkeel_model.ort"
    )

    target_compile_features(test_piper_phonemize PUBLIC cxx_std_17)

    target_include_directories(
        test_piper_phonemize PUBLIC
        "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/src>"
        ${ESPEAK_NG_DIR}/include
    )

    target_link_directories(
        test_piper_phonemize PUBLIC
        ${ESPEAK_NG_DIR}/lib
    )

    target_link_libraries(test_piper_phonemize PUBLIC
        piper_phonemize
        espeak-ng
    )
endif()

# ---- Declare install targets ----

include(GNUInstallDirs)

install(
    TARGETS piper_phonemize
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})

install(
    DIRECTORY ${CMAKE_SOURCE_DIR}/src/
    DESTINATION include/piper-phonemize
    FILES_MATCHING
    PATTERN "*.h"
    PATTERN "*.hpp")

# Install executable with platform-specific handling
if(NOT ANDROID AND NOT CMAKE_SYSTEM_NAME STREQUAL "iOS")
    install(
        TARGETS piper_phonemize_exe
        ARCHIVE DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

install(
    FILES ${CMAKE_SOURCE_DIR}/etc/libtashkeel_model.ort
    TYPE DATA)

# Dependencies
install(
    DIRECTORY ${ESPEAK_NG_DIR}/
    DESTINATION ${CMAKE_INSTALL_PREFIX})

# Install onnxruntime only if not skipped
if(NOT SKIP_ONNXRUNTIME)
    install(
        DIRECTORY ${ONNXRUNTIME_DIR}/include/
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

    install(
        DIRECTORY ${ONNXRUNTIME_DIR}/lib/
        DESTINATION ${CMAKE_INSTALL_LIBDIR})
endif()
