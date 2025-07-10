# iOS toolchain for cross-compilation
set(CMAKE_SYSTEM_NAME iOS)
set(CMAKE_SYSTEM_VERSION 12.0)
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET "12.0")

# Find iOS SDK path using xcrun
execute_process(
    COMMAND xcrun --sdk iphoneos --show-sdk-path
    OUTPUT_VARIABLE IOS_SDK_PATH
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
    RESULT_VARIABLE XCRUN_RESULT
)

if(XCRUN_RESULT EQUAL 0 AND EXISTS ${IOS_SDK_PATH})
    set(CMAKE_OSX_SYSROOT ${IOS_SDK_PATH})
    message(STATUS "iOS SDK found via xcrun: ${CMAKE_OSX_SYSROOT}")
else()
    # Try common iOS SDK locations for different Xcode versions
    set(POSSIBLE_IOS_SDKS
        "/Applications/Xcode_16.2.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk"
        "/Applications/Xcode_16.1.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk"
        "/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk"
    )
    
    foreach(SDK_PATH ${POSSIBLE_IOS_SDKS})
        if(EXISTS ${SDK_PATH})
            set(CMAKE_OSX_SYSROOT ${SDK_PATH})
            message(STATUS "iOS SDK found at: ${CMAKE_OSX_SYSROOT}")
            break()
        endif()
    endforeach()
    
    if(NOT CMAKE_OSX_SYSROOT)
        message(FATAL_ERROR "iOS SDK not found. Please install Xcode with iOS SDK or specify CMAKE_OSX_SYSROOT manually.")
    endif()
endif()

# Set compiler paths
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

# Set compiler flags with explicit iOS target and correct sysroot
set(CMAKE_C_FLAGS_INIT "-target arm64-apple-ios12.0 -isysroot ${CMAKE_OSX_SYSROOT}")
set(CMAKE_CXX_FLAGS_INIT "-target arm64-apple-ios12.0 -isysroot ${CMAKE_OSX_SYSROOT}")

# Additional iOS-specific settings
set(BUILD_SHARED_LIBS OFF)
set(CMAKE_SKIP_BUILD_RPATH ON)
set(CMAKE_SKIP_INSTALL_RPATH ON)

# Skip compiler tests for cross-compilation
set(CMAKE_C_COMPILER_WORKS 1)
set(CMAKE_CXX_COMPILER_WORKS 1)

# Find root path settings
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
