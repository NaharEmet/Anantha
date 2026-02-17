#!/usr/bin/env python3
import os
import csv
import requests
import gzip
from io import StringIO

def download_storm_data_for_year(year):
    """Download storm data for a specific year"""
    base_url = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
    filename = f"StormEvents_details-ftp_v1.0_d{year}_c20250520.csv.gz"
    
    print(f"Downloading {filename}...")
    
    try:
        url = f"{base_url}{filename}"
        response = requests.get(url, stream=True)
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
                            'Thunderstorm Wind', 'Hail', 'Marine Thunderstorm Wind']
            
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

def merge_with_existing_dataset(new_events):
    """Merge new storm events with existing dataset"""
    
    # Read existing dataset
    existing_file = 'full_disaster_dataset.csv'
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
    combined_output_file = 'full_disaster_dataset_updated.csv'
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

def main():
    # Download and process storm data for recent years
    years = ['2020', '2021', '2022', '2023']
    all_storm_events = []
    
    for year in years:
        filepath = download_storm_data_for_year(year)
        if filepath:
            storm_events = process_storm_file(filepath)
            print(f"Extracted {len(storm_events)} disaster events from {year}")
            all_storm_events.extend(storm_events)
    
    if all_storm_events:
        print(f"\nTotal storm events extracted: {len(all_storm_events)}")
        merge_with_existing_dataset(all_storm_events)
    else:
        print("No storm events data was successfully processed")

if __name__ == "__main__":
    main()
