#!/usr/bin/env python3
"""
Basic usage example for Text2Map toolkit.

This example demonstrates the complete pipeline:
1. Text processing (cleaning tweets)
2. Named Entity Recognition (extracting locations)  
3. Geocoding (converting locations to coordinates)
4. Export to GeoJSON/Shapefile
"""

import pandas as pd
from text2map.core import TweetProcessor, GeocodeTweetProcessor
from text2map.models import BERTNERInference

def basic_pipeline_example():
    """Demonstrate basic Text2Map pipeline."""
    
    # Sample data (replace with your CSV file)
    sample_data = {
        'tweet_id': [1, 2, 3],
        'created_at': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'text': [
            'RT @user: Major flooding reported in New Orleans, Louisiana',
            'Hurricane making landfall near Tampa, Florida #weather',
            'https://example.com Storm surge warning for Mobile, Alabama coast'
        ]
    }
    
    tweets_df = pd.DataFrame(sample_data)
    print(f"Sample data: {len(tweets_df)} tweets")
    
    # Step 1: Process and clean tweet text
    print("\n1. Processing tweet text...")
    processor = TweetProcessor()
    clean_tweets = processor.process_dataframe(tweets_df)
    print("Text processing complete")
    
    # Step 2: Extract locations using BERT NER
    print("\n2. Extracting locations with BERT NER...")
    try:
        ner = BERTNERInference()
        locations = ner.process_dataframe(
            clean_tweets, 
            text_column='no_multi_space_newlines',
            id_column='id'
        )
        print("Location extraction complete")
        print(f"Found entities in {locations['total_entities'].sum()} tweets")
        
    except Exception as e:
        print(f"NER processing failed: {e}")
        print("Skipping to geocoding step...")
        # Create mock location data for demonstration
        locations = clean_tweets[['id', 'no_multi_space_newlines']].copy()
        locations['gpe_entities'] = [['New Orleans'], ['Tampa'], ['Mobile']]
        locations['total_entities'] = [1, 1, 1]
    
    # Step 3: Prepare data for geocoding (mock JSONL format)
    print("\n3. Preparing data for geocoding...")
    
    # Create mock JSONL data structure
    jsonl_data = []
    for _, row in locations.iterrows():
        # Mock entity extraction results
        entities = []
        if 'New Orleans' in str(row['no_multi_space_newlines']):
            entities.append([0, 11, 'GPE'])  # Mock span for "New Orleans"
        if 'Tampa' in str(row['no_multi_space_newlines']):
            entities.append([0, 5, 'GPE'])   # Mock span for "Tampa"
        if 'Mobile' in str(row['no_multi_space_newlines']):
            entities.append([0, 6, 'GPE'])   # Mock span for "Mobile"
        
        jsonl_data.append({
            'text': row['no_multi_space_newlines'],
            'label': entities
        })
    
    # Save to temporary JSONL file
    import json
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in jsonl_data:
            f.write(json.dumps(item) + '\n')
        temp_jsonl_path = f.name
    
    # Step 4: Geocode and create maps
    print("\n4. Geocoding locations...")
    try:
        geocoder = GeocodeTweetProcessor()
        
        # Load and process the temporary JSONL file
        ner_entities = geocoder.load_data(temp_jsonl_path)
        processed_data = geocoder.process_entities(ner_entities, max_rows=10)
        geocoded_data = geocoder.geocode_data(processed_data)
        
        if len(geocoded_data) > 0:
            # Create GeoDataFrame and add state polygons
            gdf = geocoder.create_geodataframe(geocoded_data)
            gdf = geocoder.add_state_polygons(gdf)
            
            # Export to GeoJSON
            geojson_path = "data/processed/example_output.geojson"
            final_gdf = geocoder.clean_and_export_geojson(gdf, geojson_path)
            
            # Convert to Shapefile
            shapefile_path = "data/processed/example_output.shp"
            geocoder.convert_to_shapefile(geojson_path, shapefile_path)
            
            print(f"Processing complete!")
            print(f"GeoJSON saved to: {geojson_path}")
            print(f"Shapefile saved to: {shapefile_path}")
            print(f"Processed {len(final_gdf)} locations")
        else:
            print("No locations could be geocoded")
            
    except Exception as e:
        print(f"Geocoding failed: {e}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_jsonl_path):
            os.unlink(temp_jsonl_path)

def command_line_example():
    """Show how to use Text2Map from command line."""
    
    print("\n" + "="*50)
    print("COMMAND LINE USAGE EXAMPLES")
    print("="*50)
    
    print("\n1. Process tweet text:")
    print("python -m text2map.core.text_processor --input tweets.csv --output clean_tweets.csv")
    
    print("\n2. Extract locations with BERT NER:")
    print("python -m text2map.models.bert_ner --input clean_tweets.csv --output locations.csv")
    
    print("\n3. Geocode and create maps:")
    print("python -m text2map.core.geocoder --input locations.jsonl --output-dir data/processed/")
    
    print("\n4. Full pipeline with custom settings:")
    print("python -m text2map.core.text_processor --input tweets.csv --output-dir data/processed/")
    print("python -m text2map.models.bert_ner --input data/processed/tweets_wo_gt.csv --confidence 0.8")
    print("python -m text2map.core.geocoder --input locations.jsonl --states Florida Alabama --max-rows 500")

if __name__ == "__main__":
    print("Text2Map Basic Usage Example")
    print("=" * 40)
    
    try:
        basic_pipeline_example()
        command_line_example()
        
    except Exception as e:
        print(f"Example failed: {e}")
        print("Please ensure Text2Map is properly installed and data files are available.")