from apscheduler.schedulers.background import BackgroundScheduler
import time

def my_task():
    print("Task executed!")

scheduler = BackgroundScheduler()
scheduler.add_job(my_task, 'date', run_date='2024-07-30 12:00:00')
scheduler.start()

# Keep the script running to allow the scheduled task to execute
while True:
    time.sleep(1)