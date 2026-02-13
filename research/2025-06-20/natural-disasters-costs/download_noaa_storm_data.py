#!/usr/bin/env python3
import os
import requests
import gzip
import pandas as pd
from io import StringIO

def download_and_process_storm_data():
    """
    Download NOAA storm events data for recent years (2020-2023)
    and process it to supplement our existing disaster dataset
    """
    
    # Base URL for NOAA storm events
    base_url = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
    
    # Years we want to download (most recent years)
    years_to_download = ['2020', '2021', '2022', '2023']
    
    # Create directory for storm data
    storm_dir = 'noaa_storm_data'
    if not os.path.exists(storm_dir):
        os.makedirs(storm_dir)
    
    downloaded_files = []
    
    for year in years_to_download:
        # Construct filename
        filename = f"StormEvents_details-ftp_v1.0_d{year}_c20250520.csv.gz"
        filepath = os.path.join(storm_dir, filename)
        
        print(f"Downloading {filename}...")
        
        try:
            # Download the file
            url = f"{base_url}{filename}"
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save the compressed file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Successfully downloaded {filename}")
            downloaded_files.append((year, filepath))
            
        except Exception as e:
            print(f"Error downloading {filename}: {str(e)}")
            continue
    
    # Process the downloaded files
    all_storm_events = []
    
    for year, filepath in downloaded_files:
        print(f"Processing {year} storm data...")
        
        try:
            # Read the gzipped file
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                # Read the first few lines to understand the structure
                first_lines = [next(f) for _ in range(5)]
                
                # Read the full CSV
                df = pd.read_csv(StringIO(''.join(first_lines + list(f))))
                
                # Process relevant columns
                if 'BEGIN_DATE_TIME' in df.columns and 'EVENT_TYPE' in df.columns:
                    # Extract year from date
                    df['Year'] = df['BEGIN_DATE_TIME'].str.extract(r'(\d{4})')[0]
                    
                    # Filter for relevant disaster types
                    disaster_types = ['Hurricane', 'Tornado', 'Flood', 'Drought', 
                                    'Wildfire', 'Winter Storm', 'Ice Storm', 
                                    'Thunderstorm Wind', 'Hail']
                    
                    filtered_df = df[df['EVENT_TYPE'].isin(disaster_types)]
                    
                    # Create simplified entries for our dataset
                    for _, row in filtered_df.iterrows():
                        event_entry = {
                            'Year': row['Year'],
                            'Event Name': f"{row['EVENT_TYPE']} in {row.get('STATE', 'Unknown')}",
                            'Country/Region': row.get('STATE', 'United States'),
                            'Disaster Type': row['EVENT_TYPE'],
                            'Deaths': str(int(row.get('DEATHS_DIRECT', 0)) + int(row.get('DEATHS_INDIRECT', 0))),
                            'Economic Loss (USD)': str(int(row.get('DAMAGE_PROPERTY', 0)) + int(row.get('DAMAGE_CROPS', 0))),
                            'Loss as % of GDP': '0',  # Not available in this data
                            'Source': 'NOAA Storm Events',
                            'Catastrophic': 'Yes' if (int(row.get('DAMAGE_PROPERTY', 0)) + int(row.get('DAMAGE_CROPS', 0))) > 1000000 else 'No',
                            'Insured Loss (USD)': '0'  # Not available in this data
                        }
                        
                        all_storm_events.append(event_entry)
                    
                    print(f"Extracted {len(filtered_df)} disaster events from {year}")
                
        except Exception as e:
            print(f"Error processing {year} data: {str(e)}")
            continue
    
    # Convert to DataFrame and save
    if all_storm_events:
        storm_df = pd.DataFrame(all_storm_events)
        
        # Save the storm data
        storm_output_file = 'noaa_storm_events_2020_2023.csv'
        storm_df.to_csv(storm_output_file, index=False)
        print(f"Saved storm events data to {storm_output_file}")
        
        # Merge with our existing dataset
        merge_with_existing_dataset(storm_df)
    else:
        print("No storm events data was successfully processed")

def merge_with_existing_dataset(storm_df):
    """Merge the new storm data with our existing full dataset"""
    
    # Read existing dataset
    existing_file = 'full_disaster_dataset.csv'
    if not os.path.exists(existing_file):
        print(f"Existing dataset {existing_file} not found")
        return
    
    existing_df = pd.read_csv(existing_file)
    
    # Combine datasets
    combined_df = pd.concat([existing_df, storm_df], ignore_index=True)
    
    # Remove duplicates based on Year, Event Name, and Country/Region
    combined_df = combined_df.drop_duplicates(subset=['Year', 'Event Name', 'Country/Region'], keep='first')
    
    # Sort by year
    combined_df = combined_df.sort_values('Year')
    
    # Save combined dataset
    combined_output_file = 'full_disaster_dataset_updated.csv'
    combined_df.to_csv(combined_output_file, index=False)
    
    print(f"\nDataset Summary:")
    print(f"  Original dataset: {len(existing_df)} events")
    print(f"  New storm events: {len(storm_df)} events")
    print(f"  Combined dataset: {len(combined_df)} events")
    print(f"  Updated dataset saved to: {combined_output_file}")

if __name__ == "__main__":
    download_and_process_storm_data()
