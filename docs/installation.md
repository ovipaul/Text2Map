# Text2Map Installation and Usage Guide

## Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Clone and Install
```bash
git clone https://github.com/yourusername/Text2Map.git
cd Text2Map
pip install -e .
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Project Structure

```
Text2Map/
├── README.md                   # Main documentation
├── requirements.txt            # Python dependencies
├── setup.py                   # Package installation
├── LICENSE                    # MIT license
├── .gitignore                 # Git ignore rules
├── config/
│   └── default_config.yaml    # Configuration settings
├── src/text2map/              # Main package
│   ├── __init__.py
│   ├── core/                  # Core processing modules
│   │   ├── __init__.py
│   │   ├── text_processor.py  # Tweet text cleaning
│   │   └── geocoder.py        # Geocoding and mapping
│   ├── models/                # Machine learning models
│   │   ├── __init__.py
│   │   └── bert_ner.py        # BERT NER inference
│   ├── visualization/         # Mapping and visualization
│   │   └── __init__.py
│   └── utils/                 # Utilities and helpers
│       └── __init__.py
├── data/                      # Data storage
│   ├── boundaries/            # Geographic boundaries
│   │   ├── countries/         # Natural Earth country data
│   │   ├── counties/          # US Census county data
│   │   └── cities/            # 500 Cities urban data
│   ├── models/                # Pre-trained models
│   │   └── bert_ner/          # BERT NER model files
│   └── processed/             # Output data (created at runtime)
├── examples/                  # Usage examples
│   └── basic_usage.py         # Basic pipeline example
├── tests/                     # Test suite
│   └── __init__.py
└── docs/                      # Documentation
```

## Quick Start

### 1. Text Processing
Clean raw tweet text by removing RT, handles, emojis, and links:

```bash
python -m text2map.core.text_processor --input raw_tweets.csv --output clean_tweets.csv
```

### 2. Named Entity Recognition
Extract location entities using the fine-tuned BERT model:

```bash
python -m text2map.models.bert_ner --input clean_tweets.csv --output locations.csv
```

### 3. Geocoding and Mapping
Convert locations to coordinates and create maps:

```bash
python -m text2map.core.geocoder --input locations.jsonl --output-dir results/
```

## Python API Usage

```python
from text2map.core import TweetProcessor, GeocodeTweetProcessor
from text2map.models import BERTNERInference
import pandas as pd

# Load your data
tweets_df = pd.read_csv("tweets.csv")

# 1. Clean text
processor = TweetProcessor()
clean_tweets = processor.process_dataframe(tweets_df)

# 2. Extract locations
ner = BERTNERInference()
locations = ner.process_dataframe(clean_tweets, text_column='no_multi_space_newlines')

# 3. Geocode (requires JSONL format for now)
geocoder = GeocodeTweetProcessor()
# ... additional processing steps
```

## Data Requirements

### Input Formats
- **Text Processing**: CSV with columns `tweet_id`, `created_at`, `text`
- **NER**: CSV with columns `id`, `text`
- **Geocoding**: JSONL with `text` and `label` fields

### Output Formats
- **Processed Text**: CSV with cleaned text
- **NER Results**: CSV with extracted entities
- **Geocoded Data**: GeoJSON and Shapefile formats

## Model Files

The BERT NER model is located at `data/models/bert_ner/` and includes:
- `pytorch_model.bin`: The trained model weights
- `config.json`: Model configuration
- `tokenizer.json`: Tokenizer configuration

## Geographic Boundaries

The toolkit includes three levels of geographic boundaries:
1. **Countries**: Natural Earth 110m cultural boundaries
2. **Counties**: US Census county boundaries  
3. **Cities**: 500 Cities project urban boundaries

## Configuration

Edit `config/default_config.yaml` to customize:
- Model paths and parameters
- Geocoding settings
- Output formats and directories
- Visualization parameters

## Troubleshooting

### Common Issues

1. **Model Not Found**: Ensure `data/models/bert_ner/` contains the model files
2. **Boundary Files Missing**: Check that boundary shapefiles are in `data/boundaries/`
3. **Memory Errors**: Reduce batch sizes in configuration
4. **Geocoding Limits**: Add delays between requests to respect API limits

### Debug Mode
Add `--verbose` flag to commands for detailed logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.