import pandas as pd
import re
import argparse
import os

class TweetProcessor:
    """
    Process tweets by cleaning text: remove RT, handles, emojis, links, and normalize spaces.
    Outputs cleaned tweets ready for further NER processing.
    """
    
    def __init__(self):
        """Initialize the tweet processor."""
        # Emoji pattern for removal
        self.emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"  # miscellaneous symbols
            u"\U000024C2-\U0001F251"  # enclosed characters
            u"\U00010000-\U0010FFFF"  # supplementary planes
            "]+", 
            flags=re.UNICODE
        )
    
    def remove_rt(self, text):
        """Function to remove 'RT' if it's the first word."""
        if isinstance(text, str) and text.startswith("RT "):
            return text[3:]
        return text if isinstance(text, str) else ""
    
    def remove_first_handle(self, text):
        """Function to remove '@handle:' if it's the first word in the text."""
        if not isinstance(text, str):
            return ""
        text = re.sub(r'^@\w+:\s*', '', text)
        return text
    
    def remove_emojis(self, text):
        """Remove emojis from text using regex pattern."""
        if not isinstance(text, str):
            return ""
        return self.emoji_pattern.sub(r'', text)
    
    def remove_links(self, text):
        """Remove HTTP/HTTPS URLs from text."""
        if not isinstance(text, str):
            return ""
        return re.sub(r'http\S+', '', text)
    
    def remove_space_newlines(self, text):
        """Replace newlines with spaces and normalize multiple spaces."""
        if not isinstance(text, str):
            return ""
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def process_dataframe(self, df):
        """
        Process the entire dataframe through all cleaning steps.
        
        Args:
            df: DataFrame with columns 'tweet_id', 'created_at', 'text'
            
        Returns:
            Processed DataFrame with cleaned text
        """
        print(f"Processing {len(df)} tweets...")
        
        # Rename columns to match notebook pattern
        tweet = df[['tweet_id', 'created_at', 'text']].rename(columns={
            'tweet_id': 'id',
            'created_at': 'time', 
            'text': 'tweet'
        })
        
        # Step 1: Remove RT
        print("Step 1: Removing RT...")
        tweet['no_rt_text'] = tweet['tweet'].apply(self.remove_rt)
        
        # Step 2: Remove first handle
        print("Step 2: Removing first handle...")
        tweet['no_handle'] = tweet['no_rt_text'].apply(self.remove_first_handle)
        
        # Step 3: Remove emojis
        print("Step 3: Removing emojis...")
        tweet['no_emoji_text'] = tweet['no_handle'].apply(self.remove_emojis)
        
        # Step 4: Remove links
        print("Step 4: Removing links...")
        tweet['no_links'] = tweet['no_emoji_text'].apply(self.remove_links)
        
        # Step 5: Normalize spaces and newlines
        print("Step 5: Normalizing spaces and newlines...")
        tweet['no_multi_space_newlines'] = tweet['no_links'].apply(self.remove_space_newlines)
        
        print("Processing complete!")
        return tweet
    
    def save_processed_tweets(self, tweet_df, output_path):
        """
        Save processed tweets to CSV file.
        
        Args:
            tweet_df: Processed DataFrame
            output_path: Path to save the CSV file
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        tweet_df[['id', 'time', 'no_multi_space_newlines']].to_csv(output_path, index=False)
        print(f"Processed tweets saved to: {output_path}")

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Process tweets by cleaning text (remove RT, handles, emojis, links)")
    
    parser.add_argument("--input", "-i", required=True, help="Input CSV file (e.g., francine.csv)")
    parser.add_argument("--output", "-o", help="Output CSV file (default: data/processed/{input_name}_wo_gt.csv)")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory (default: data/processed)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return
    
    if not args.output:
        input_name = os.path.splitext(os.path.basename(args.input))[0]
        args.output = os.path.join(args.output_dir, f"{input_name}_wo_gt.csv")
    
    print(f"Loading data from: {args.input}")
    try:
        df = pd.read_csv(args.input, encoding='utf-8')
        print(f"Loaded {len(df)} tweets")
        
        required_columns = ['tweet_id', 'created_at', 'text']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return
            
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return
    
    processor = TweetProcessor()
    
    try:
        processed_tweet_df = processor.process_dataframe(df)
        processor.save_processed_tweets(processed_tweet_df, args.output)
        
        print(f"\n=== PROCESSING SUMMARY ===")
        print(f"Total tweets processed: {len(processed_tweet_df)}")
        print(f"Output saved to: {args.output}")
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return

if __name__ == "__main__":
    main()