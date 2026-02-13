#!/usr/bin/env python3
import os

def debug_filename_parsing():
    storm_dir = 'noaa_storm_data'
    if not os.path.exists(storm_dir):
        print(f"No storm data directory found at {storm_dir}")
        return
    
    print("Debugging filename parsing:")
    for filename in os.listdir(storm_dir):
        if filename.endswith('.gz'):
            print(f"\nFilename: {filename}")
            
            # Extract all digits and find the most likely year
            all_digits = ''.join(filter(str.isdigit, filename))
            print(f"  All digits in filename: {all_digits}")
            
            # Look for 4-digit sequences that could be years
            possible_years = []
            for i in range(len(all_digits) - 3):
                year_candidate = all_digits[i:i+4]
                year = int(year_candidate)
                # Check if it's a reasonable year
                if 1970 <= year <= 2023:
                    possible_years.append(year_candidate)
            
            if possible_years:
                # Take the first reasonable year found
                year = int(possible_years[0])
                print(f"  Found possible year: {year}")
            else:
                print("  No reasonable years found")
            
            # Try to find the pattern in the filename
            if '_d' in filename:
                parts = filename.split('_d')
                print(f"  Parts after '_d': {parts}")
                if len(parts) > 1:
                    after_d = parts[1]
                    print(f"  Content after '_d': '{after_d}'")
                    # Find first 4 digits
                    for i in range(len(after_d) - 3):
                        if after_d[i:i+4].isdigit():
                            year = int(after_d[i:i+4])
                            if 1970 <= year <= 2023:
                                print(f"  Found year: {year}")
                                break

if __name__ == "__main__":
    debug_filename_parsing()
