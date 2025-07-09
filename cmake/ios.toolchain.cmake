# iOS toolchain for cross-compilation
set(CMAKE_SYSTEM_NAME iOS)
set(CMAKE_SYSTEM_VERSION 11.0)
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0")

# Force iOS SDK without falling back to macOS
set(CMAKE_OSX_SYSROOT "iphoneos")

# Set compiler paths
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

# Set compiler flags with explicit iOS target (no macabi)
set(CMAKE_C_FLAGS_INIT "-target arm64-apple-ios11.0 -isysroot ${CMAKE_OSX_SYSROOT}")
set(CMAKE_CXX_FLAGS_INIT "-target arm64-apple-ios11.0 -isysroot ${CMAKE_OSX_SYSROOT}")

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
