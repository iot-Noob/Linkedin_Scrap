# main_logging.py
import logging
import os

if not os.path.exists("./logs"):
    os.mkdir("logs")

logging.basicConfig(
    filename="logs/scraper.log",  # Log file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def logging_func(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Finished {func.__name__}")
            logging.info(f"result:::: {result}")  
            return result
            
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper
