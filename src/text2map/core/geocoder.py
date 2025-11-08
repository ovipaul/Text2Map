import json
import pandas as pd
import geopandas as gpd
import argparse
import os
from collections import Counter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from shapely.geometry import Point

class GeocodeTweetProcessor:
    """
    Process tweet NER entities and geocode locations up to GeoJSON and Shapefile export.
    No visualization - just data processing and geocoding.
    """
    
    def __init__(self, shapefile_path=None):
        """Initialize with shapefile path for state boundaries."""
        if shapefile_path is None:
            shapefile_path = os.path.join(os.path.dirname(__file__), "../../data/boundaries/countries/ne_110m_admin_1_states_provinces.shp")
        
        self.shapefile_path = shapefile_path
        self.geolocator = Nominatim(user_agent="text2map_geocoder")
        self.us_states = [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", 
            "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", 
            "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", 
            "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", 
            "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", 
            "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", 
            "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
        ]
        self.us_states_lower = [state.lower() for state in self.us_states]
    
    def load_data(self, file_path):
        """Load NER entities from JSONL file."""
        print(f"Loading data from: {file_path}")
        ner_entities = pd.read_json(path_or_buf=file_path, lines=True)
        print(f"Loaded {len(ner_entities)} tweets")
        return ner_entities
    
    def extract_entities_by_type(self, row):
        """Extract FAC, LOC, GPE entities from NER labels."""
        fac = []
        loc = []
        gpe = []
        
        for start, end, entity_type in row['label']:
            entity_text = row['text'][start:end]
            if entity_type == "FAC":
                fac.append(entity_text)
            elif entity_type == "LOC":
                loc.append(entity_text)
            elif entity_type == "GPE":
                gpe.append(entity_text)
        
        return {"FAC": fac, "LOC": loc, "GPE": gpe}
    
    def process_entities(self, ner_entities, max_rows=300):
        """Process and clean extracted entities."""
        print("Processing entities...")
        
        ner_entities['extracted_entities'] = ner_entities.apply(self.extract_entities_by_type, axis=1)
        
        ner_entities['FAC'] = ner_entities['extracted_entities'].apply(lambda x: list(set(x['FAC'])))
        ner_entities['LOC'] = ner_entities['extracted_entities'].apply(lambda x: list(set(x['LOC'])))
        ner_entities['GPE'] = ner_entities['extracted_entities'].apply(lambda x: list(set(x['GPE'])))
        
        def remove_fac_loc_duplicates(row):
            row['FAC'] = [entity for entity in row['FAC'] if entity not in row['LOC']]
            return row
        
        ner_entities = ner_entities.apply(remove_fac_loc_duplicates, axis=1)
        
        ner_entities['FAC'] = ner_entities['FAC'].apply(lambda x: ', '.join(sorted(x)))
        ner_entities['LOC'] = ner_entities['LOC'].apply(lambda x: ', '.join(sorted(x)))
        ner_entities['GPE'] = ner_entities['GPE'].apply(lambda x: ', '.join(sorted(x)))
        
        result_df = ner_entities[['FAC', 'LOC', 'GPE']]
        result_df = result_df.dropna(subset=['FAC', 'LOC', 'GPE'], how='all')
        
        columns_to_clean = ['FAC', 'LOC', 'GPE']
        def remove_hash(value):
            if isinstance(value, str):
                return value.replace('#', '')
            return value
        
        result_df[columns_to_clean] = result_df[columns_to_clean].applymap(remove_hash)
        
        df_cleaned = result_df.groupby(["FAC", "LOC", "GPE"]).size().reset_index(name='count')
        
        for col in ["FAC", "LOC", "GPE"]:
            df_cleaned[col] = df_cleaned[col].str.strip(" ,")
        
        df_cleaned = df_cleaned.iloc[1:].reset_index(drop=True)
        data = df_cleaned[:max_rows] if max_rows else df_cleaned
        
        print(f"Processed {len(data)} unique location combinations")
        return data
    
    def geocode_address(self, row):
        """Geocode address from FAC, LOC, GPE components."""
        try:
            address = f"{row['FAC']}, {row['LOC']}, {row['GPE']}"
            location = self.geolocator.geocode(address, timeout=10)
            if location:
                return pd.Series([location.latitude, location.longitude])
            else:
                return pd.Series([None, None])
        except GeocoderTimedOut:
            return pd.Series([None, None])
    
    def geocode_data(self, data):
        """Apply geocoding to all rows."""
        print("Geocoding addresses...")
        data[['Latitude', 'Longitude']] = data.apply(self.geocode_address, axis=1)
        
        df = pd.DataFrame(data)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        print(f"Successfully geocoded {len(df)} locations")
        
        return df
    
    def create_geodataframe(self, df, target_states=None):
        """Create GeoDataFrame and filter by target states."""
        geometry = [Point(xy) for xy in zip(df['Longitude'], df['Latitude'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        
        if target_states:
            print(f"Filtering data for states: {target_states}")
            
            cultural_gdf = gpd.read_file(self.shapefile_path)
            selected_states = cultural_gdf[cultural_gdf['name'].isin(target_states)]
            
            if gdf.crs != selected_states.crs:
                selected_states = selected_states.to_crs(gdf.crs)
            
            filtered_gdf = gpd.sjoin(gdf, selected_states, how='inner', predicate='within')
            columns_to_keep = ['FAC', 'LOC', 'GPE', 'count', 'Latitude', 'Longitude', 'geometry']
            gdf = filtered_gdf[columns_to_keep]
            
            print(f"Filtered to {len(gdf)} locations within target states")
        
        return gdf
    
    def contains_us_state_exact(self, gpe_value):
        """Check if GPE contains only a valid U.S. state name."""
        if pd.isna(gpe_value):
            return False
        gpe_lower = str(gpe_value).lower().strip()
        return gpe_lower in self.us_states_lower
    
    def add_state_polygons(self, gdf):
        """Add state polygon geometries for state-only entries."""
        print("Adding state polygons...")
        
        gdf['make_polygon'] = gdf.apply(
            lambda row: 1 if (row['FAC'] == '' and row['LOC'] == '' and self.contains_us_state_exact(row['GPE'])) else 0, 
            axis=1
        )
        
        cultural_gdf = gpd.read_file(self.shapefile_path)
        cultural_gdf['name'] = cultural_gdf['name'].str.lower()
        
        gdf['GPE_lower'] = gdf['GPE'].str.lower().str.strip()
        gdf = gdf.merge(
            cultural_gdf[['name', 'geometry']],
            left_on='GPE_lower',
            right_on='name',
            how='left'
        )
        
        gdf.loc[gdf['make_polygon'] == 1, 'geometry'] = gdf.loc[gdf['make_polygon'] == 1, 'geometry_y']
        gdf = gdf.drop(columns=['GPE_lower', 'name', 'geometry_y'], errors='ignore')
        
        polygon_count = len(gdf[gdf['make_polygon'] == 1])
        print(f"Added {polygon_count} state polygons")
        
        return gdf
    
    def clean_and_export_geojson(self, gdf, output_path="data/processed/geometry.geojson"):
        """Clean geometry columns and export to GeoJSON."""
        print("Cleaning geometry and exporting to GeoJSON...")
        
        gdf1 = gdf.copy()
        gdf1 = gdf1.set_geometry("geometry")
        
        columns_to_drop = [col for col in gdf1.columns if col.startswith('geometry_') and col != 'geometry']
        if columns_to_drop:
            gdf1 = gdf1.drop(columns=columns_to_drop)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        gdf1.to_file(output_path, driver="GeoJSON")
        print(f"Exported cleaned GeoDataFrame to: {output_path}")
        
        return gdf1
    
    def convert_to_shapefile(self, geojson_path, shapefile_path=None):
        """Convert GeoJSON to Shapefile."""
        print("Converting GeoJSON to Shapefile...")
        
        if shapefile_path is None:
            base_name = os.path.splitext(geojson_path)[0]
            shapefile_path = f"{base_name}.shp"
        
        gdf = gpd.read_file(geojson_path)
        gdf.to_file(shapefile_path, driver='ESRI Shapefile')
        
        print(f"GeoJSON converted to Shapefile successfully!")
        print(f"Shapefile saved to: {shapefile_path}")
        
        return shapefile_path

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Process and geocode tweet locations to GeoJSON and Shapefile")
    
    parser.add_argument("--input", "-i", required=True, help="Input JSONL file with NER data")
    parser.add_argument("--shapefile", help="Shapefile path")
    parser.add_argument("--states", nargs="+", help="Target states to filter (e.g., Florida Georgia)")
    parser.add_argument("--max-rows", type=int, default=300, help="Maximum rows to process")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    parser.add_argument("--geojson-name", default="geometry.geojson", help="GeoJSON output filename")
    parser.add_argument("--shapefile-name", help="Shapefile output filename")
    parser.add_argument("--skip-shapefile", action="store_true", help="Skip shapefile conversion")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    processor = GeocodeTweetProcessor(args.shapefile)
    
    ner_entities = processor.load_data(args.input)
    processed_data = processor.process_entities(ner_entities, args.max_rows)
    geocoded_data = processor.geocode_data(processed_data)
    gdf = processor.create_geodataframe(geocoded_data, args.states)
    gdf = processor.add_state_polygons(gdf)
    
    geojson_path = os.path.join(args.output_dir, args.geojson_name)
    final_gdf = processor.clean_and_export_geojson(gdf, geojson_path)
    
    if not args.skip_shapefile:
        if args.shapefile_name:
            shapefile_path = os.path.join(args.output_dir, args.shapefile_name)
        else:
            base_name = os.path.splitext(args.geojson_name)[0]
            shapefile_path = os.path.join(args.output_dir, f"{base_name}.shp")
        
        processor.convert_to_shapefile(geojson_path, shapefile_path)
    
    csv_path = os.path.join(args.output_dir, "processed_locations.csv")
    final_gdf.to_csv(csv_path, index=False)
    print(f"Processed data also saved to: {csv_path}")
    
    print(f"\nProcessing complete!")
    print(f"Total locations processed: {len(final_gdf)}")

if __name__ == "__main__":
    main()