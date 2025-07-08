# iOS toolchain for cross-compilation
set(CMAKE_SYSTEM_NAME iOS)
set(CMAKE_SYSTEM_VERSION 11.0)
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0")

# Set iOS SDK path
execute_process(
    COMMAND xcrun --show-sdk-path --sdk iphoneos
    OUTPUT_VARIABLE CMAKE_OSX_SYSROOT
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)

message(STATUS "iOS toolchain: Initial SDK path from xcrun: ${CMAKE_OSX_SYSROOT}")

# Fallback if xcrun fails
if(NOT CMAKE_OSX_SYSROOT)
    # Try to find the latest iOS SDK
    execute_process(
        COMMAND find /Applications -name "iPhoneOS*.sdk" -type d
        OUTPUT_VARIABLE IOS_SDK_SEARCH
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    
    if(IOS_SDK_SEARCH)
        # Get the first (typically latest) SDK found
        string(REGEX REPLACE "\n.*" "" FIRST_SDK "${IOS_SDK_SEARCH}")
        set(CMAKE_OSX_SYSROOT "${FIRST_SDK}")
        message(STATUS "iOS toolchain: Using found SDK: ${CMAKE_OSX_SYSROOT}")
    else()
        # Final fallback
        set(CMAKE_OSX_SYSROOT "/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk")
        message(STATUS "iOS toolchain: Using fallback SDK: ${CMAKE_OSX_SYSROOT}")
    endif()
endif()

message(STATUS "iOS toolchain: Final SDK path: ${CMAKE_OSX_SYSROOT}")

# Set compiler paths
set(CMAKE_C_COMPILER xcrun)
set(CMAKE_CXX_COMPILER xcrun)
set(CMAKE_C_COMPILER_ARG1 clang)
set(CMAKE_CXX_COMPILER_ARG1 clang++)

# Set compiler flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fembed-bitcode -arch arm64")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fembed-bitcode -arch arm64")

# Set library types - force static libraries for iOS
set(BUILD_SHARED_LIBS OFF)
set(CMAKE_SKIP_BUILD_RPATH ON)
set(CMAKE_SKIP_INSTALL_RPATH ON)

# Skip compiler tests for cross-compilation
set(CMAKE_C_COMPILER_WORKS 1)
set(CMAKE_CXX_COMPILER_WORKS 1)

# Additional iOS-specific settings
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
