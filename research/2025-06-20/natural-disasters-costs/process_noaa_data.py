#!/usr/bin/env python3
import csv
import os

def process_noaa_data():
    # Read the NOAA billion-dollar disasters data
    noaa_file = 'noaa_billion_dollar_disasters.csv'
    
    # Process the NOAA data to extract disaster events
    with open(noaa_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        # Initialize data structure
        disasters = []
        
        # Track year totals for each disaster type
        year_totals = {}
        
        # Process each row (state, drought, flooding, freeze, severe storm, tropical cyclone, wildfire, winter storm)
        for row in reader:
            state = row[0]
            
            # Skip totals row
            if state == 'US':
                continue
                
            # Process each disaster type
            disaster_types = ['Drought', 'Flood', 'Freeze', 'Severe Storm', 'Tropical Cyclone', 'Wildfire', 'Winter Storm']
            
            for i, disaster_type in enumerate(disaster_types):
                try:
                    cost = float(row[i+1]) if row[i+1] != '' else 0
                    if cost > 0:  # Only include if there's a cost
                        year = 2024  # The data is from 1980-2024
                        
                        # Create a generic event name
                        event_name = f"{disaster_type} in {state}"
                        
                        # Create entry for our main dataset
                        disaster_entry = {
                            'Year': year,
                            'Event Name': event_name,
                            'Country/Region': state,
                            'Disaster Type': disaster_type,
                            'Deaths': '0',  # Death data not available in this file
                            'Economic Loss (USD)': str(cost * 1000000),  # Convert millions to dollars
                            'Loss as % of GDP': '0',  # Not available in this file
                            'Source': 'NOAA',
                            'Catastrophic': 'Yes' if cost > 1000 else 'No',
                            'Insured Loss (USD)': '0'  # Not available in this file
                        }
                        
                        disasters.append(disaster_entry)
                except (ValueError, IndexError):
                    continue
    
    # Write processed data to a new CSV
    output_file = 'noaa_processed_disasters.csv'
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Year', 'Event Name', 'Country/Region', 'Disaster Type', 
            'Deaths', 'Economic Loss (USD)', 'Loss as % of GDP', 
            'Source', 'Catastrophic', 'Insured Loss (USD)'
        ])
        
        writer.writeheader()
        writer.writerows(disasters)
    
    print(f"Processed {len(disasters)} disaster events from NOAA data")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    process_noaa_data()
