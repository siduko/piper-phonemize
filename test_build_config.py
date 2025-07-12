#!/usr/bin/env python3
"""
Test script to validate that build configurations work correctly for different platforms.
"""

import os
import sys
import tempfile
import shutil
import subprocess

def test_android_patch():
    """Test that Android builds still get UCD library linking."""
    print("Testing Android patch behavior...")
    
    # Get current directory first
    original_dir = os.getcwd()
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy patch script to temp directory
        shutil.copy(os.path.join(original_dir, 'patch_espeak.py'), temp_dir)
        
        # Create a mock CMakeLists.txt for espeak-ng
        os.makedirs(os.path.join(temp_dir, 'src', 'libespeak-ng'), exist_ok=True)
        cmake_content = """
add_library(espeak-ng STATIC
    espeak_api.c
    synth_mbrola.c
)

target_include_directories(espeak-ng PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
"""
        
        with open(os.path.join(temp_dir, 'src', 'libespeak-ng', 'CMakeLists.txt'), 'w') as f:
            f.write(cmake_content)
        
        # Run patch without iOS environment (simulates Android)
        os.chdir(temp_dir)
        result = subprocess.run([sys.executable, 'patch_espeak.py'], 
                              capture_output=True, text=True)
        
        # Check that UCD linking was NOT added (for Android, it's handled in main CMakeLists.txt)
        with open(os.path.join(temp_dir, 'src', 'libespeak-ng', 'CMakeLists.txt'), 'r') as f:
            patched_content = f.read()
        
        if 'target_link_libraries(espeak-ng' in patched_content:
            print("❌ FAIL: Android build would get UCD linking (should be handled separately)")
            print("Patched content:", patched_content)
            return False
        else:
            print("✅ PASS: Android build preserved (UCD linking handled in main CMakeLists.txt)")
            return True

def test_ios_patch():
    """Test that iOS builds get UCD library linking in espeak-ng."""
    print("Testing iOS patch behavior...")
    
    # Get current directory first
    original_dir = os.getcwd()
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy patch script to temp directory
        shutil.copy(os.path.join(original_dir, 'patch_espeak.py'), temp_dir)
        
        # Create a mock CMakeLists.txt for espeak-ng
        os.makedirs(os.path.join(temp_dir, 'src', 'libespeak-ng'), exist_ok=True)
        cmake_content = """
add_library(espeak-ng STATIC
    espeak_api.c
    synth_mbrola.c
)

target_include_directories(espeak-ng PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
"""
        
        with open(os.path.join(temp_dir, 'src', 'libespeak-ng', 'CMakeLists.txt'), 'w') as f:
            f.write(cmake_content)
        
        # Set iOS environment variables
        env = os.environ.copy()
        env['CMAKE_SYSTEM_NAME'] = 'iOS'
        env['PLATFORM_NAME'] = 'iphoneos'
        
        # Run patch with iOS environment
        os.chdir(temp_dir)
        result = subprocess.run([sys.executable, 'patch_espeak.py'], 
                              capture_output=True, text=True, env=env)
        
        # Check that UCD linking was added for iOS
        with open(os.path.join(temp_dir, 'src', 'libespeak-ng', 'CMakeLists.txt'), 'r') as f:
            patched_content = f.read()
        
        if 'target_link_libraries(espeak-ng PRIVATE ucd)' in patched_content:
            print("✅ PASS: iOS build gets UCD linking in espeak-ng")
            return True
        else:
            print("❌ FAIL: iOS build did not get UCD linking")
            print("Patched content:", patched_content)
            print("Patch output:", result.stdout)
            print("Patch errors:", result.stderr)
            return False

def main():
    """Run all tests."""
    print("Testing build configuration patches...")
    print("=" * 50)
    
    android_ok = test_android_patch()
    print()
    ios_ok = test_ios_patch()
    
    print()
    print("=" * 50)
    if android_ok and ios_ok:
        print("✅ All tests passed! Build configurations are correct.")
        return 0
    else:
        print("❌ Some tests failed. Check the build configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
