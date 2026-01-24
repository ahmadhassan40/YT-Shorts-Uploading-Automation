import logging
import os
from typing import List
from main import Pipeline

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, topics_file="topics.txt"):
        """Initialize batch processor with a file of topics"""
        self.topics_file = topics_file
        self.topics = self.load_topics()
        self.failed_topics = []
        self.successful_topics = []
        
    def load_topics(self) -> List[str]:
        """Load topics from file, one per line"""
        if not os.path.exists(self.topics_file):
            logger.warning(f"Topics file not found: {self.topics_file}")
            return self.get_topics_interactive()
        
        # Ask user if they want to use file or enter topics manually
        print(f"\n📄 Found topics file: {self.topics_file}")
        choice = input("Use topics from file? (y/n): ").strip().lower()
        
        if choice == 'y':
            with open(self.topics_file, 'r', encoding='utf-8') as f:
                topics = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            logger.info(f"Loaded {len(topics)} topics from {self.topics_file}")
            return topics
        else:
            return self.get_topics_interactive()
    
    def get_topics_interactive(self) -> List[str]:
        """Get topics interactively from user input"""
        print("\n" + "="*60)
        print("🎬 BATCH VIDEO GENERATOR")
        print("="*60)
        print("Enter topics one by one. Press Enter on empty line to finish.\n")
        
        topics = []
        while True:
            topic = input(f"Topic #{len(topics) + 1} (or press Enter to finish): ").strip()
            if not topic:
                break
            topics.append(topic)
            print(f"  ✅ Added: {topic}")
        
        if not topics:
            print("\n⚠️  No topics entered. Exiting...")
            return []
        
        print(f"\n📋 Total topics to process: {len(topics)}")
        confirm = input("Proceed with generation? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Cancelled.")
            return []
        
        return topics
    
    def process_all(self):
        """Process all topics in the list"""
        if not self.topics:
            logger.error("No topics to process")
            return
        
        pipeline = Pipeline()
        
        # Create error log file
        error_log_path = "batch_errors.log"
        
        for i, topic in enumerate(self.topics, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing topic {i}/{len(self.topics)}: {topic}")
            logger.info(f"{'='*60}\n")
            
            try:
                pipeline.run(topic)
                self.successful_topics.append(topic)
                logger.info(f"✅ Successfully completed: {topic}")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"❌ Failed: {topic}")
                logger.error(f"Error: {e}")
                logger.error(f"Full traceback:\n{error_details}")
                
                # Save to error log file
                with open(error_log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Topic: {topic}\n")
                    f.write(f"Error: {e}\n")
                    f.write(f"Traceback:\n{error_details}\n")
                    f.write(f"{'='*60}\n")
                
                self.failed_topics.append((topic, str(e)))
        
        # Summary
        self.print_summary()
        
        if self.failed_topics:
            logger.info(f"\nDetailed errors saved to: {error_log_path}")
    
    def print_summary(self):
        """Print batch processing summary"""
        total = len(self.topics)
        success_count = len(self.successful_topics)
        fail_count = len(self.failed_topics)
        
        print("\n" + "="*60)
        print("BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"Total topics: {total}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {fail_count}")
        
        if self.failed_topics:
            print("\nFailed Topics:")
            for topic, error in self.failed_topics:
                print(f"  - {topic}: {error}")
        
        print("="*60 + "\n")

def main():
    """Run batch processor"""
    processor = BatchProcessor("topics.txt")
    processor.process_all()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
