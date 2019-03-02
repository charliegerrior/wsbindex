from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger

from rq import Queue
from worker import conn
#NEED TO UPDATE
from run import *

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

sched = BlockingScheduler(timezone="America/New_York")

q = Queue(connection=conn)

#NEED TO UPDATE
def inverse_wsb():
 q.enqueue(run_inverse_wsb, job_timeout=23500 )
 
def rebalance():
  q.enqueue(run_rebalance, job_timeout=300)
  
def updates():
  q.enqueue(run_orderupdates, job_timeout=-1)

#def gather_comments():
# q.enqueue(run_gather_comments)

#sched.add_job(gather_comments) #enqueue right away once
#sched.add_job(gather_comments, 'interval', minutes=1)
#sched.add_job(gather_threads) #enqueue right away once
#sched.add_job(gather_threads, 'interval', minutes=30)
trigger = OrTrigger([
    #CronTrigger(day_of_week='mon-fri'),
    CronTrigger(day_of_week='mon-fri', hour='9', minute='30-59/10'),
    CronTrigger(day_of_week='mon-fri', hour='10-15', minute='*/10')
])
sched.add_job(inverse_wsb, 'cron', day_of_week='mon-fri', hour=9, minute=30)
sched.add_job(updates)
#sched.add_job(rebalance, 'interval', minutes=10)
sched.add_job(rebalance, trigger)
sched.start()