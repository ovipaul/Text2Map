import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import pandas as pd
import argparse
import os
from typing import List, Dict, Any
import json

class BERTNERInference:
    """BERT NER inference for location and event extraction from tweets."""
    
    def __init__(self, model_path: str = None):
        """
        Initialize BERT NER model for inference.
        
        Args:
            model_path: Path to trained BERT model directory
        """
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "../../data/models/bert_ner")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForTokenClassification.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"Loaded model from: {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Trying to load bert-base-cased tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
            self.model = AutoModelForTokenClassification.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
        
        self.ner_pipeline = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1,
            aggregation_strategy="simple"
        )
        
        self.id2label = self._load_label_mapping(model_path)
        self.entity_classes = self._get_entity_classes()
        
        print(f"Available entity classes: {list(self.entity_classes.keys())}")
    
    def _load_label_mapping(self, model_path: str) -> Dict[int, str]:
        """Load label mapping from config."""
        config_path = os.path.join(model_path, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                if "id2label" in config:
                    return {int(k): v for k, v in config["id2label"].items()}
            except Exception as e:
                print(f"Could not load config: {e}")
        
        return {
            0: "O",
            1: "B-GPE", 
            2: "I-GPE",
            3: "B-EVENT",
            4: "I-EVENT"
        }
    
    def _get_entity_classes(self) -> Dict[str, List[str]]:
        """Get available entity classes from label mapping."""
        classes = {}
        for label in self.id2label.values():
            if label != "O":
                class_name = label.split("-")[-1]
                if class_name not in classes:
                    classes[class_name] = []
                classes[class_name].append(label)
        return classes
    
    def extract_entities(self, text: str, confidence_threshold: float = 0.5) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities from text."""
        if not text or not isinstance(text, str):
            return {class_name: [] for class_name in self.entity_classes.keys()}
        
        try:
            entities = self.ner_pipeline(text)
            grouped_entities = {class_name: [] for class_name in self.entity_classes.keys()}
            
            for entity in entities:
                if entity['score'] >= confidence_threshold:
                    label = entity['entity_group'].upper()
                    class_name = label.split("-")[-1] if "-" in label else label
                    
                    if class_name in grouped_entities:
                        grouped_entities[class_name].append({
                            'text': entity['word'],
                            'label': label,
                            'confidence': entity['score'],
                            'start': entity.get('start', 0),
                            'end': entity.get('end', 0)
                        })
            
            return grouped_entities
            
        except Exception as e:
            print(f"Error processing text: {e}")
            return {class_name: [] for class_name in self.entity_classes.keys()}
    
    def process_dataframe(
        self, 
        df: pd.DataFrame, 
        text_column: str = 'text',
        id_column: str = 'id',
        confidence_threshold: float = 0.5
    ) -> pd.DataFrame:
        """Process DataFrame to extract entities."""
        results = []
        
        print(f"Processing {len(df)} tweets...")
        
        for idx, row in df.iterrows():
            tweet_id = row[id_column]
            text = str(row[text_column]) if pd.notna(row[text_column]) else ""
            
            entities = self.extract_entities(text, confidence_threshold)
            
            result_row = {
                'id': tweet_id,
                'text': text
            }
            
            for class_name in self.entity_classes.keys():
                class_entities = entities.get(class_name, [])
                result_row[f'{class_name.lower()}_entities'] = [e['text'] for e in class_entities]
                result_row[f'{class_name.lower()}_count'] = len(class_entities)
                result_row[f'{class_name.lower()}_confidence'] = [e['confidence'] for e in class_entities]
            
            result_row['total_entities'] = sum(len(entities.get(c, [])) for c in self.entity_classes.keys())
            results.append(result_row)
            
            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1}/{len(df)} tweets")
        
        return pd.DataFrame(results)
    
    def save_results(self, df: pd.DataFrame, output_path: str) -> None:
        """Save results to CSV."""
        df_save = df.copy()
        
        for col in df_save.columns:
            if col.endswith('_entities') or col.endswith('_confidence'):
                df_save[col] = df_save[col].apply(
                    lambda x: '; '.join([str(item) for item in x]) if x else ''
                )
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        df_save.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Results saved to: {output_path}")

def main():
    """Main inference function."""
    parser = argparse.ArgumentParser(description="BERT NER Inference")
    
    parser.add_argument("--model-path", "-m", help="Path to trained model directory")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file")
    parser.add_argument("--output", "-o", help="Output CSV file")
    parser.add_argument("--text-column", default="text", help="Text column name")
    parser.add_argument("--id-column", default="id", help="ID column name")
    parser.add_argument("--confidence", type=float, default=0.5, help="Confidence threshold")
    
    args = parser.parse_args()
    
    if not args.output:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}_bert_ner.csv"
    
    print(f"Loading data from: {args.input}")
    df = pd.read_csv(args.input, encoding='utf-8')
    print(f"Loaded {len(df)} tweets")
    
    inferencer = BERTNERInference(args.model_path)
    results_df = inferencer.process_dataframe(df, args.text_column, args.id_column, args.confidence)
    inferencer.save_results(results_df, args.output)
    
    total_entities = results_df['total_entities'].sum()
    tweets_with_entities = len(results_df[results_df['total_entities'] > 0])
    
    print(f"\n=== INFERENCE SUMMARY ===")
    print(f"Total tweets processed: {len(results_df)}")
    print(f"Tweets with entities: {tweets_with_entities}")
    print(f"Total entities found: {total_entities}")

if __name__ == "__main__":
    main()