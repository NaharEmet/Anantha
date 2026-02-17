#!/usr/bin/env python3
import os
import csv
import gzip
from io import StringIO
import time

def process_storm_file(filepath):
    """Process a storm data file and extract disaster events"""
    try:
        # Read the gzipped file
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            # Read CSV data
            reader = csv.DictReader(f)
            
            # Process rows and extract disaster events
            storm_events = []
            disaster_types = ['Hurricane', 'Tornado', 'Flood', 'Drought', 
                            'Wildfire', 'Winter Storm', 'Ice Storm', 
                            'Thunderstorm Wind', 'Hail', 'Marine Thunderstorm Wind',
                            'Heavy Rain', 'Heavy Snow', 'Blizzard',
                            'Coastal Flood', 'River Flood', 'Flash Flood', 'Lake-Effect Snow']
            
            for row in reader:
                event_type = row.get('EVENT_TYPE', '').strip()
                if event_type in disaster_types:
                    # Create simplified entry
                    event_entry = {
                        'Year': row.get('YEAR', ''),
                        'Event Name': f"{event_type} in {row.get('STATE', 'Unknown')}",
                        'Country/Region': row.get('STATE', 'United States'),
                        'Disaster Type': event_type,
                        'Deaths': str(int(row.get('DEATHS_DIRECT', 0)) + int(row.get('DEATHS_INDIRECT', 0))),
                        'Economic Loss (USD)': convert_damage_value(row.get('DAMAGE_PROPERTY', 0)) + convert_damage_value(row.get('DAMAGE_CROPS', 0)),
                        'Loss as % of GDP': '0',
                        'Source': 'NOAA Storm Events',
                        'Catastrophic': 'Yes' if (convert_damage_value(row.get('DAMAGE_PROPERTY', 0)) + convert_damage_value(row.get('DAMAGE_CROPS', 0))) > 1000000 else 'No',
                        'Insured Loss (USD)': '0'
                    }
                    
                    storm_events.append(event_entry)
            
            return storm_events
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return []

def convert_damage_value(damage_str):
    """Convert damage value string to numeric (handles K/M suffixes)"""
    try:
        if not damage_str or damage_str.strip() == '':
            return 0
        
        damage_str = damage_str.strip()
        
        # Handle K (thousands) and M (millions) suffixes
        if damage_str.endswith('K'):
            return int(float(damage_str[:-1]) * 1000)
        elif damage_str.endswith('M'):
            return int(float(damage_str[:-1]) * 1000000)
        else:
            return int(float(damage_str))
    except:
        return 0

def process_all_existing_files():
    """Process all existing storm data files"""
    storm_dir = 'noaa_storm_data'
    if not os.path.exists(storm_dir):
        print(f"No storm data directory found at {storm_dir}")
        return
    
    all_events = []
    year_counts = {}
    
    for filename in os.listdir(storm_dir):
        if filename.endswith('.gz'):
            filepath = os.path.join(storm_dir, filename)
            
            # Extract year from filename
            try:
                # Extract all digits and find the most likely year
                all_digits = ''.join(filter(str.isdigit, filename))
                
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
                else:
                    year = None
                    
                if year is None:
                    print(f"Could not extract year from filename: {filename}")
                    continue
            except:
                print(f"Could not extract year from filename: {filename}")
                continue
            
            print(f"Processing {filename} for year {year}...")
            events = process_storm_file(filepath)
            
            if events:
                print(f"Extracted {len(events)} disaster events from {year}")
                all_events.extend(events)
                year_counts[year] = len(events)
    
    print(f"\nTotal events extracted from existing files: {len(all_events)}")
    print("Events by year:")
    for year, count in sorted(year_counts.items()):
        print(f"  {year}: {count} events")
    
    if all_events:
        merge_with_existing_dataset(all_events)

def merge_with_existing_dataset(new_events):
    """Merge new storm events with existing dataset"""
    
    # Read existing dataset
    existing_file = 'full_disaster_dataset_updated.csv'
    if not os.path.exists(existing_file):
        print(f"Existing dataset {existing_file} not found")
        return
    
    existing_events = []
    with open(existing_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_events.append(row)
    
    # Combine datasets
    all_events = existing_events + new_events
    
    # Remove duplicates based on Year, Event Name, and Country/Region
    unique_events = {}
    for event in all_events:
        key = (event['Year'], event['Event Name'], event['Country/Region'])
        if key not in unique_events:
            unique_events[key] = event
    
    # Convert back to list and sort by year
    combined_events = sorted(unique_events.values(), key=lambda x: x['Year'])
    
    # Save combined dataset
    combined_output_file = 'full_disaster_dataset_all_storms.csv'
    with open(combined_output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Year', 'Event Name', 'Country/Region', 'Disaster Type', 
            'Deaths', 'Economic Loss (USD)', 'Loss as % of GDP', 
            'Source', 'Catastrophic', 'Insured Loss (USD)'
        ])
        
        writer.writeheader()
        writer.writerows(combined_events)
    
    print(f"\nDataset Summary:")
    print(f"  Original dataset: {len(existing_events)} events")
    print(f"  New storm events: {len(new_events)} events")
    print(f"  Combined dataset: {len(combined_events)} events")
    print(f"  Updated dataset saved to: {combined_output_file}")
    
    # Print summary by year
    year_counts = {}
    for event in combined_events:
        year = event['Year']
        year_counts[year] = year_counts.get(year, 0) + 1
    
    print("\nDisaster counts by year (recent years):")
    for year in sorted(year_counts.keys())[-10:]:
        print(f"  {year}: {year_counts[year]} disasters")
    
    # Print summary by disaster type
    type_counts = {}
    for event in combined_events:
        disaster_type = event['Disaster Type']
        type_counts[disaster_type] = type_counts.get(disaster_type, 0) + 1
    
    print("\nTop disaster types:")
    for disaster_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {disaster_type}: {count} events")

if __name__ == "__main__":
    process_all_existing_files()
