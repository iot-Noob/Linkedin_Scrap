from linkedin_scrap import WebScraper
import schedule
import toml
import sys
import os
import re
from email_sender import MailSender
import time
from main_logging import logging_func,logging
from datetime import datetime
import pandas as pd

ctz= "Asia/Karachi"
try:
    # Search for the first .toml file
    for root, _, files in os.walk("./"):
        for f in files:
            if f.endswith(".toml"):
                found = True
                mp = os.path.join(root, f)
                break
        if found:
            break

    if not found:
        print("Error: Cannot find config.toml. Please make a config.toml in the same directory.")
        sys.exit(1)

    # Load TOML file
    with open(mp, "r") as f:
        cfg = toml.load(f)

        if "email-config" not in cfg or "recipient" not in cfg["email-config"]:
            raise ValueError("Missing 'recipient' in [email-config] section of config.toml")
        email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")

        recipients = cfg["email-config"]["recipient"]
        if not isinstance(recipients, list) or not all(isinstance(email, str) and email_pattern.match(email) for email in recipients):
            raise ValueError("Each recipient must be a valid email address string in the [email-config] section")
        if not cfg["output_paths"] or not cfg["output_paths"]["main_csv_path"]:
            raise ValueError("Error load toml missing `[output_paths]` or `main_csv_path` in outut path")
    print("✅ Config loaded and validated successfully in main!")


except Exception as e:
    print(f"❌ Failed to load or validate config.toml: {e}")
    sys.exit()

@logging_func

def main_job():
    try:
        sj = WebScraper()
        scdir = cfg["output_paths"]["main_csv_path"]
        
        # Create output directory if needed
        os.makedirs(scdir, exist_ok=True)
        
        # Collect all jobs first
        all_jobs = []
        for job in sj.get_jobs():  # Changed from jdata to job
            if job:  # Now using the correct variable name
                all_jobs.append(job)
            if not all_jobs:
                print("⏩ No jobs found")
                logging.info("No jobs collected")
                return  # Prevent job references
        
        # Build email body only if jobs found
        if all_jobs:
            email_body = """
            <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; font-size: 16px; color: #212529; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 700px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 6px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
                <h2 style="color: #007bff; margin-bottom: 20px;">Linkedin jobs, Python,React JS , AI, and Data Science Jobs in Lahore</h2>
                <p style="margin-top: 0;">Dear Candidate,</p>
                <p>Please find below a curated list of recent  </strong>:</p>
            """

            # Add jobs to email body
            for i, job in enumerate(all_jobs, 1):
                email_body += f"""
                <div style="margin-bottom: 25px; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px; background-color: #fefefe;">
                <h4 style="margin-top: 0; margin-bottom: 5px; font-size: 18px;">
                    <a href="{job['url']}" target="_blank" style="color: #007bff; text-decoration: none;">
                    {i}. {job['title']}
                    </a>
                </h4>
                <div style="font-style: italic; color: #6c757d; margin-bottom: 10px;">at {job['company_name']}</div>
                <ul style="list-style: none; padding-left: 0; margin: 0;">
                    <li><strong>Location:</strong> {job['location']}</li>
                    <li><strong>Time:</strong> {job['posted_time']}</li>
                </ul>
                </div>
                """

            # Add closing to email body
            email_body += """
                <p style="margin-top: 40px;">Best regards,<br>Talha Automated Job Hunter</p>
                </div>
                </body>
                </html>
            """

            # Send email once
            ms = MailSender()
            for r in recipients:
                ms.send_mail(
                    recipient_email=r,
                    subject="Linked in List of Python/AI/ML ReactJS Job Opportunities in Lahore",
                    body=email_body
                )

            # Save CSV once
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{scdir}/job_listings_{timestamp}.csv"
            pd.DataFrame(all_jobs).to_csv(output_file, index=False, encoding='utf-8')
            print(f"✅ Jobs saved to CSV: {output_file}")
            all_jobs=[]
        else:
            print("No jobs found in this run")
            logging.info("No jobs found in this run")
    except Exception as e:
        print(f"error in main due to {e}")
    finally:
        sj.cleanup_driver()
if __name__=="__main__":
    try:
        # main_job()
      
        schedule.every().monday.at("08:00").do(main_job)
        schedule.every().monday.at("12:00").do(main_job)
        schedule.every().monday.at("18:00").do(main_job)

        # Tuesday
        schedule.every().tuesday.at("09:00").do(main_job)
        schedule.every().tuesday.at("11:00").do(main_job)
        schedule.every().tuesday.at("17:00").do(main_job)

        # Wednesday
        schedule.every().wednesday.at("08:00").do(main_job)
        schedule.every().wednesday.at("13:00").do(main_job)
        schedule.every().wednesday.at("18:00").do(main_job)

        # Thursday
        schedule.every().thursday.at("09:00").do(main_job)
        schedule.every().thursday.at("15:00").do(main_job)
        schedule.every().thursday.at("19:00").do(main_job)

        # Friday
        schedule.every().friday.at("07:00").do(main_job)
        schedule.every().friday.at("12:00").do(main_job)
        schedule.every().friday.at("17:00").do(main_job)

        # Saturday
        schedule.every().saturday.at("10:00").do(main_job)
        schedule.every().saturday.at("14:00").do(main_job)
        schedule.every().saturday.at("18:00").do(main_job)

        # Sunday
        schedule.every().sunday.at("08:00").do(main_job)
        schedule.every().sunday.at("11:00").do(main_job)
        schedule.every().sunday.at("16:00").do(main_job)
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(20)  # Check every minute
 
    except Exception as e:
       
        print(f"Error occur {e}")
 