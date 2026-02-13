#!/usr/bin/env python3
import csv
import os

def merge_datasets():
    # Input files
    sample_file = 'sample_disaster_dataset.csv'
    noaa_file = 'noaa_processed_disasters.csv'
    output_file = 'full_disaster_dataset.csv'
    
    # Read the sample dataset
    sample_disasters = []
    with open(sample_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_disasters.append(row)
    
    # Read the NOAA processed data
    noaa_disasters = []
    with open(noaa_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            noaa_disasters.append(row)
    
    # Combine datasets
    all_disasters = sample_disasters + noaa_disasters
    
    # Sort by year
    all_disasters.sort(key=lambda x: x['Year'])
    
    # Write merged dataset
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Year', 'Event Name', 'Country/Region', 'Disaster Type', 
            'Deaths', 'Economic Loss (USD)', 'Loss as % of GDP', 
            'Source', 'Catastrophic', 'Insured Loss (USD)'
        ])
        
        writer.writeheader()
        writer.writerows(all_disasters)
    
    print(f"Successfully merged datasets:")
    print(f"  Sample disasters: {len(sample_disasters)}")
    print(f"  NOAA disasters: {len(noaa_disasters)}")
    print(f"  Total disasters: {len(all_disasters)}")
    print(f"  Saved to {output_file}")
    
    # Print summary by year
    year_counts = {}
    for disaster in all_disasters:
        year = disaster['Year']
        year_counts[year] = year_counts.get(year, 0) + 1
    
    print("\nDisaster counts by year:")
    for year in sorted(year_counts.keys()):
        print(f"  {year}: {year_counts[year]} disasters")

if __name__ == "__main__":
    merge_datasets()
