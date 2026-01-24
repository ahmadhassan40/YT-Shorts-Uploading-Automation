import schedule
import time
import logging
from datetime import datetime
from batch_processor import BatchProcessor
from main import Pipeline
from config.config_loader import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Scheduler")

def run_daily_batch():
    """Run batch processing job"""
    logger.info("⏰ Starting scheduled batch job...")
    
    # Check if we should use auto-generated topics
    auto_generate = config.get("scheduler.auto_generate_topics", False)
    topics_count = config.get("scheduler.topics_per_run", 5)
    
    if auto_generate:
        logger.info(f"🤖 Auto-generating {topics_count} trending topics...")
        topics = generate_trending_topics(topics_count)
        
        # Create temporary topics file
        with open("auto_topics.txt", "w", encoding="utf-8") as f:
            for topic in topics:
                f.write(f"{topic}\n")
        
        processor = BatchProcessor("auto_topics.txt")
    else:
        processor = BatchProcessor("topics.txt")
    
    try:
        processor.process_all()
        logger.info("✅ Scheduled batch job completed")
    except Exception as e:
        logger.error(f"❌ Scheduled batch job failed: {e}")

def generate_trending_topics(count=5):
    """Generate trending topics using Ollama"""
    from engines.script_engine import OllamaScriptEngine
    
    topics = []
    categories = ["Technology", "History", "Science", "Nature", "Space"]
    
    for i in range(count):
        category = categories[i % len(categories)]
        # Simple topic generation - could be enhanced
        topic = f"Amazing {category} Facts"
        topics.append(topic)
    
    return topics

def run_single_video(topic=None):
    """Run single video generation"""
    if not topic:
        topic = config.get("scheduler.default_topic", "Trending Topic of the Day")
    
    logger.info(f"⏰ Starting scheduled video for topic: {topic}")
    try:
        pipeline = Pipeline()
        pipeline.run(topic)
        logger.info(f"✅ Scheduled video completed: {topic}")
    except Exception as e:
        logger.error(f"❌ Scheduled video failed: {e}")

def start_scheduler():
    """Start the scheduler based on configuration"""
    enabled = config.get("scheduler.enabled", False)
    
    if not enabled:
        logger.warning("Scheduler is disabled in settings.yaml")
        print("\n💡 To enable:")
        print("   1. Edit config/settings.yaml")
        print("   2. Set scheduler.enabled: true")
        print("   3. Run again\n")
        return
    
    run_time = config.get("scheduler.run_time", "09:00")
    mode = config.get("scheduler.mode", "batch")  # 'batch' or 'single'
    
    logger.info(f"🕐 Scheduler started!")
    logger.info(f"   Mode: {mode}")
    logger.info(f"   Daily run time: {run_time}")
    
    if mode == "batch":
        auto_gen = config.get("scheduler.auto_generate_topics", False)
        if auto_gen:
            logger.info(f"   Topics: Auto-generated ({config.get('scheduler.topics_per_run', 5)} per day)")
        else:
            logger.info(f"   Topics: From topics.txt")
        schedule.every().day.at(run_time).do(run_daily_batch)
    else:
        schedule.every().day.at(run_time).do(run_single_video)
    
    # Keep the scheduler running
    logger.info("Waiting for scheduled time...")
    logger.info("Press Ctrl+C to stop\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    start_scheduler()
