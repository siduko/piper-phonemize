#!/usr/bin/env python3
"""
Simple test to verify Android builds are not affected by iOS patches.
"""

import os
import tempfile
import subprocess
import sys

# Test Android (no iOS environment variables)
print("Testing Android patch (no iOS env vars)...")
result = subprocess.run([sys.executable, 'patch_espeak.py'], 
                      capture_output=True, text=True, cwd='.')

if "iOS build detected: False" in result.stdout:
    print("✅ PASS: Android build correctly detected")
else:
    print("❌ FAIL: Android build detection issue")
    print("Output:", result.stdout)

# Test iOS (with environment variables)
print("\nTesting iOS patch (with iOS env vars)...")
env = os.environ.copy()
env['CMAKE_SYSTEM_NAME'] = 'iOS'
env['PLATFORM_NAME'] = 'iphoneos'

result = subprocess.run([sys.executable, 'patch_espeak.py'], 
                      capture_output=True, text=True, env=env, cwd='.')

if "iOS build detected: True" in result.stdout:
    print("✅ PASS: iOS build correctly detected")
else:
    print("❌ FAIL: iOS build detection issue")
    print("Output:", result.stdout)

print("\nTest completed. Android builds should be preserved.")
