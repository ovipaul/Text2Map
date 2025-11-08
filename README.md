# Text2Map: Geospatial Analysis from Social Media Text

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Text2Map is a comprehensive toolkit for extracting geospatial insights from social media text data. It combines Natural Language Processing (NER), geocoding, and interactive visualization to transform textual location mentions into dynamic spatial-temporal maps.

## Features

### Core Functionality
- **Text Processing**: Clean and preprocess social media text (remove RT, handles, emojis, links)
- **Named Entity Recognition**: Extract location entities (GPE, LOC, FAC) using fine-tuned BERT models
- **Geocoding**: Convert text locations to geographic coordinates using multiple geocoding services
- **Visualization**: Generate interactive heatmaps and time-series animations
- **Temporal Analysis**: Create cumulative and time-binned geospatial visualizations

### Advanced Features
- **Animation Generation**: Create GIF animations showing geospatial patterns over time
- **Multi-scale Boundaries**: Support for country, state, county, and city-level analysis
- **Social Media Integration**: Built-in Twitter/X API client for data collection
- **Configurable Pipeline**: YAML-based configuration for easy customization

## Installation

### Requirements
- Python 3.8+
- CUDA-compatible GPU (recommended for BERT inference)

### Quick Install
```bash
git clone https://github.com/yourusername/Text2Map.git
cd Text2Map
pip install -e .
```

### Development Install
```bash
git clone https://github.com/yourusername/Text2Map.git
cd Text2Map
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage
```python
from text2map.core import TweetProcessor, GeocodeTweetProcessor
from text2map.models import BERTNERInference

# Process tweets
processor = TweetProcessor()
clean_tweets = processor.process_dataframe(tweets_df)

# Extract locations using BERT NER
ner = BERTNERInference()
locations = ner.process_dataframe(clean_tweets)

# Geocode locations
geocoder = GeocodeTweetProcessor()
geo_data = geocoder.geocode_data(locations)
```

### Command Line Interface
```bash
# Process Twitter data end-to-end
python -m text2map.core.text_processor --input tweets.csv --output clean_tweets.csv

# Extract locations using BERT NER
python -m text2map.models.bert_ner --input clean_tweets.csv --output locations.csv

# Geocode and generate maps
python -m text2map.core.geocoder --input locations.jsonl --output data/processed/
```

## Example Workflows

### Hurricane Event Analysis
```python
from text2map.core import TweetProcessor, GeocodeTweetProcessor
from text2map.models import BERTNERInference

# 1. Process raw tweets
processor = TweetProcessor()
clean_tweets = processor.process_dataframe(hurricane_tweets)

# 2. Extract locations
ner = BERTNERInference(model_path="data/models/bert_ner")
locations = ner.process_dataframe(clean_tweets)

# 3. Geocode locations
geocoder = GeocodeTweetProcessor()
geo_data = geocoder.geocode_data(locations)
```

### Disaster Response Monitoring
- Track mention clusters during emergency events
- Analyze temporal evolution of affected areas
- Generate real-time situation awareness maps

## Architecture

### Pipeline Components

1. **Text Processing** (`text2map.core.text_processor`)
   - Social media text cleaning
   - Noise removal (RT, handles, emojis, links)
   - Text normalization

2. **Named Entity Recognition** (`text2map.models.bert_ner`)
   - BERT-based location extraction
   - Support for GPE, LOC, FAC entity types
   - Confidence scoring and filtering

3. **Geocoding** (`text2map.core.geocoder`)
   - Multiple geocoding service integration
   - Batch processing capabilities
   - Error handling and retry logic

4. **Visualization** (`text2map.visualization`)
   - Interactive heatmap generation
   - Time-series animation creation
   - Multi-scale boundary overlays

### Data Flow
```
Raw Text → Text Processing → NER → Geocoding → Visualization
    ↓           ↓              ↓        ↓           ↓
  CSV/JSON   Clean Text   Entities  Coordinates  Maps/GIFs
```

## Project Structure

```
Text2Map/
├── src/text2map/          # Main package
│   ├── core/              # Core processing modules
│   │   ├── text_processor.py     # Tweet text cleaning
│   │   └── geocoder.py           # Geocoding and mapping
│   ├── models/            # Machine learning models
│   │   └── bert_ner.py           # BERT NER inference
│   ├── visualization/     # Mapping and visualization
│   └── utils/             # Utilities and helpers
├── data/                  # Data storage
│   ├── boundaries/        # Geographic boundaries
│   │   ├── countries/     # Country-level boundaries
│   │   ├── counties/      # County-level boundaries
│   │   └── cities/        # City-level boundaries
│   ├── models/           # Pre-trained models
│   │   └── bert_ner/     # BERT NER model
│   └── processed/        # Output data
├── examples/             # Usage examples
├── tests/               # Test suite
├── docs/               # Documentation
└── config/             # Configuration files
```

## Configuration

### Default Paths
- **BERT Model**: `data/models/bert_ner/`
- **Boundaries**: `data/boundaries/`
- **Output**: `data/processed/`

### Custom Configuration
```python
# Custom model path
ner = BERTNERInference(model_path="path/to/custom/model")

# Custom boundary files
geocoder = GeocodeTweetProcessor(shapefile_path="path/to/states.shp")
```

## Data Sources

The toolkit uses several geographic boundary datasets:

1. **Natural Earth**: Country and state boundaries (`data/boundaries/countries/`)
2. **US Census**: County boundaries (`data/boundaries/counties/`)
3. **500 Cities**: City boundaries (`data/boundaries/cities/`)

## Documentation

- [Installation Guide](docs/installation.md)
- [API Reference](docs/api_reference.md)
- [Tutorial Notebooks](examples/)
- [Configuration Options](docs/configuration.md)

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_text_processor.py

# Run with coverage
pytest --cov=text2map tests/
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/yourusername/Text2Map.git
cd Text2Map
pip install -e ".[dev]"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



## Acknowledgments

- **Natural Earth**: Free vector and raster map data
- **Hugging Face Transformers**: BERT model implementation
- **GeoPandas**: Geospatial data processing
- **Nominatim**: Geocoding services

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/Text2Map/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Text2Map/discussions)

---

**Text2Map** - Transform text into maps, reveal spatial stories
