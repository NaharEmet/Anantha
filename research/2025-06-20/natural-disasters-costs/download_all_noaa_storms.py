#!/usr/bin/env python3
import os
import csv
import requests
import gzip
from io import StringIO
import time
import glob

def download_storm_data_for_year(year):
    """Download storm data for a specific year"""
    base_url = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
    filename = f"StormEvents_details-ftp_v1.0_d{year}_c20250520.csv.gz"
    
    print(f"Downloading {filename}...")
    
    try:
        url = f"{base_url}{filename}"
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Create directory for storm data
        storm_dir = 'noaa_storm_data'
        if not os.path.exists(storm_dir):
            os.makedirs(storm_dir)
        
        filepath = os.path.join(storm_dir, filename)
        
        # Save the compressed file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded {filename}")
        return filepath
        
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")
        return None

def check_existing_storm_files():
    """Check what storm files already exist"""
    storm_dir = 'noaa_storm_data'
    if not os.path.exists(storm_dir):
        return []
    
    existing_files = []
    for filename in os.listdir(storm_dir):
        if filename.endswith('.gz'):
            # Extract year from filename
            year = filename.split('_d')[1].split('_')[0]
            existing_files.append(int(year))
    
    return existing_files

def main():
    # Get existing files to avoid re-downloading
    existing_years = check_existing_storm_files()
    print(f"Found {len(existing_years)} existing storm data files")
    
    # Download and process storm data for years 1970-2023
    years = [y for y in range(1970, 2024) if y not in existing_years]
    print(f"Need to download data for {len(years)} years: {years}")
    
    if not years:
        print("All data already downloaded. Processing...")
        # If all files exist, process them all
        process_existing_files()
        return
    
    for i, year in enumerate(years):
        print(f"\nProcessing year {year} ({i+1}/{len(years)})...")
        
        filepath = download_storm_data_for_year(year)
        if filepath:
            # Process the file immediately
            storm_events = process_storm_file(filepath)
            print(f"Extracted {len(storm_events)} disaster events from {year}")
            save_year_events(year, storm_events)
        
        # Add a delay to avoid overwhelming the server
        if i % 5 == 0 and i > 0:
            print("Taking a short break to avoid overloading the server...")
            time.sleep(5)

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

def save_year_events(year, events):
    """Save events for a specific year to a CSV file"""
    if not events:
        return
    
    filename = f"noaa_storm_events_{year}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Year', 'Event Name', 'Country/Region', 'Disaster Type', 
            'Deaths', 'Economic Loss (USD)', 'Loss as % of GDP', 
            'Source', 'Catastrophic', 'Insured Loss (USD)'
        ])
        
        writer.writeheader()
        writer.writerows(events)
    
    print(f"Saved {len(events)} events to {filename}")

def process_existing_files():
    """Process all existing storm data files"""
    storm_dir = 'noaa_storm_data'
    if not os.path.exists(storm_dir):
        return
    
    all_events = []
    
    for filename in os.listdir(storm_dir):
        if filename.endswith('.gz'):
            filepath = os.path.join(storm_dir, filename)
            year = int(filename.split('_d')[1].split('_')[0])
            
            print(f"Processing {filename} for year {year}...")
            events = process_storm_file(filepath)
            
            if events:
                save_year_events(year, events)
                all_events.extend(events)
    
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

if __name__ == "__main__":
    main()
