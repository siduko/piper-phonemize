#!/usr/bin/env python3
import re
import os
import glob

def patch_cmake_files():
    """Remove all references to espeak-ng-bin executable from CMakeLists.txt and .cmake files, and fix iOS compatibility issues."""
    
    # Find all CMakeLists.txt, .cmake, and .c files
    cmake_files = []
    cmake_files.extend(glob.glob('**/CMakeLists.txt', recursive=True))
    cmake_files.extend(glob.glob('**/*.cmake', recursive=True))
    cmake_files.extend(glob.glob('**/src/libespeak-ng/spect.c', recursive=True))
    
    for cmake_file in cmake_files:
        if os.path.exists(cmake_file):
            print(f"Patching {cmake_file}")
            
            with open(cmake_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Handle C source files differently
            if cmake_file.endswith('.c'):
                # Fix iOS endianness issues in spect.c
                if 'spect.c' in cmake_file:
                    # Add compatibility macros for iOS
                    ios_compat = '''#ifdef __APPLE__
#include <libkern/OSByteOrder.h>
#define le16toh(x) OSSwapLittleToHostInt16(x)
#define le32toh(x) OSSwapLittleToHostInt32(x)
#endif

'''
                    # Insert after the first #include
                    if '#include' in content and 'OSByteOrder.h' not in content:
                        content = re.sub(r'(#include[^\n]*\n)', r'\1' + ios_compat, content, count=1)
                
                # Only write back if content changed
                if content != original_content:
                    with open(cmake_file, 'w') as f:
                        f.write(content)
                    print(f"  -> Patched successfully")
                else:
                    print(f"  -> No changes needed")
                continue
            
            # Handle CMake files (existing logic)
            
            # Remove add_executable for espeak-ng-bin
            content = re.sub(r'add_executable\s*\(\s*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove target_link_libraries for espeak-ng-bin
            content = re.sub(r'target_link_libraries\s*\(\s*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove target_include_directories for espeak-ng-bin
            content = re.sub(r'target_include_directories\s*\(\s*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove target_compile_definitions for espeak-ng-bin
            content = re.sub(r'target_compile_definitions\s*\(\s*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove set_target_properties for espeak-ng-bin
            content = re.sub(r'set_target_properties\s*\(\s*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove target_link_options for espeak-ng-bin
            content = re.sub(r'target_link_options\s*\(\s*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove target_sources for espeak-ng-bin
            content = re.sub(r'target_sources\s*\(\s*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove install commands that target espeak-ng-bin
            content = re.sub(r'install\s*\([^)]*TARGETS[^)]*espeak-ng-bin[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove custom targets that reference espeak-ng
            content = re.sub(r'add_custom_target\s*\([^)]*espeak-ng[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove lines with generator expressions that reference espeak-ng-bin
            content = re.sub(r'[^\n]*\$<TARGET_FILE:espeak-ng-bin>[^\n]*\n?', '', content)
            content = re.sub(r'[^\n]*\$<TARGET_NAME:espeak-ng-bin>[^\n]*\n?', '', content)
            
            # Fix linking issues: ensure ucd library is linked to espeak-ng
            if 'src/libespeak-ng/CMakeLists.txt' in cmake_file:
                # For iOS and static builds, ensure all dependencies are linked into espeak-ng
                if 'target_link_libraries' in content and 'espeak-ng' in content:
                    # Find the target_link_libraries block for espeak-ng and ensure ucd is included
                    if 'ucd' not in content:
                        content = re.sub(
                            r'(target_link_libraries\s*\(\s*espeak-ng)(\s+[^)]*)?(\))',
                            r'\1\2 ucd\3',
                            content,
                            flags=re.MULTILINE | re.DOTALL
                        )
                else:
                    # If no target_link_libraries exists, create one
                    # Look for the add_library command and add linking after it
                    if 'add_library' in content and 'espeak-ng' in content:
                        content = re.sub(
                            r'(add_library\s*\(\s*espeak-ng[^)]*\)[^\n]*\n)',
                            r'\1\n# Link UCD library for iOS/static builds\ntarget_link_libraries(espeak-ng PRIVATE ucd)\n',
                            content,
                            flags=re.MULTILINE | re.DOTALL
                        )
            
            # For root CMakeLists.txt, ensure UCD subdirectory is built but executable is disabled
            if cmake_file.endswith('CMakeLists.txt') and 'src/ucd-tools' in content:
                # Ensure ucd-tools is built but disable any executables
                content = re.sub(r'add_subdirectory\s*\(\s*src/ucd-tools\s*\)', 'add_subdirectory(src/ucd-tools)', content)
                # Also patch the ucd-tools CMakeLists.txt to only build library
                if 'src/ucd-tools/CMakeLists.txt' in cmake_file:
                    # Remove executable targets from ucd-tools if they exist
                    content = re.sub(r'add_executable\s*\([^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
                    content = re.sub(r'install\s*\([^)]*TARGETS[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove add_custom_command blocks that contain espeak-ng-bin dependencies or use ESPEAK_RUN_CMD
            # This is more complex - we need to remove entire add_custom_command blocks
            # that have espeak-ng-bin in their DEPENDS section or use ESPEAK_RUN_CMD
            lines = content.split('\n')
            filtered_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Check if this line starts an add_custom_command that we need to remove
                if 'add_custom_command(' in line and i < len(lines) - 1:
                    # Look ahead to see if this command block contains espeak-ng-bin references
                    j = i
                    command_block = []
                    paren_count = line.count('(') - line.count(')')
                    command_block.append(line)
                    j += 1
                    
                    # Collect the entire command block
                    while j < len(lines) and paren_count > 0:
                        next_line = lines[j]
                        command_block.append(next_line)
                        paren_count += next_line.count('(') - next_line.count(')')
                        j += 1
                    
                    # Check if this command block references espeak-ng-bin or ESPEAK_RUN_CMD
                    command_text = '\n'.join(command_block)
                    if ('espeak-ng-bin' in command_text or 'TARGET_FILE:espeak-ng-bin' in command_text or 
                        'ESPEAK_RUN_CMD' in command_text):
                        # Skip this entire command block
                        print(f"  -> Removing add_custom_command block referencing espeak-ng-bin or ESPEAK_RUN_CMD")
                        i = j
                        continue
                
                filtered_lines.append(line)
                i += 1
            
            content = '\n'.join(filtered_lines)
            
            # Also remove any remaining references to ESPEAK_RUN_CMD variable definitions
            content = re.sub(r'set\s*\(\s*ESPEAK_RUN_CMD[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove add_custom_target for 'data' that depends on compiled data files
            content = re.sub(r'add_custom_target\s*\(\s*data\s+ALL[^)]*\)', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Remove test and data subdirectories
            content = re.sub(r'add_subdirectory\s*\(\s*tests\s*\)', '', content)
            content = re.sub(r'add_subdirectory\s*\(\s*data\s*\)', '', content)
            
            # Remove speechPlayer subdirectory - this causes C++ header issues on iOS
            content = re.sub(r'add_subdirectory\s*\(\s*src/speechPlayer\s*\)', '', content)
            content = re.sub(r'add_subdirectory\s*\(\s*speechPlayer\s*\)', '', content)
            
            # Clean up multiple empty lines
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            
            # Only write back if content changed
            if content != original_content:
                with open(cmake_file, 'w') as f:
                    f.write(content)
                print(f"  -> Patched successfully")
            else:
                print(f"  -> No changes needed")

if __name__ == "__main__":
    patch_cmake_files()
