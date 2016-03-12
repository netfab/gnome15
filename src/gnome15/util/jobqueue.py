#  Gnome15 - Suite of tools for the Logitech G series keyboards and headsets
#  Copyright (C) 2010 Brett Smith <tanktarta@blueyonder.co.uk>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import Queue
import threading
import traceback
import sys
import gobject
import time
from threading import RLock
from threading import local

# Can be adjusted to speed up time to aid debugging.
TIME_FACTOR=1

# Logging
import logging
logger = logging.getLogger(__name__)

# Thread local to allow threads to detect what queue they are on
queue_names = local()

def get_current_queue():
    if hasattr(queue_names, 'queue_name'):
        return  queue_names.queue_name 
    return "None"

def is_on_queue(queue_name):
    """
    Get if the current thread came from the queue with the specified name
    
    Keyword arguments:
    queue_name        -- queue name
    """
    if hasattr(queue_names, 'queue_name') and queue_names.queue_name == queue_name:
        return True
    return False

class GTimer:    
    def __init__(self, scheduler, task_queue, task_name, interval, function, stack, *args):
        self.function = function
        if function == None:
            logger.warning("Attempt to run empty job %s on %s", task_name, task_queue.name)
            traceback.print_stack()
            return
        self.stack = stack
        self.scheduler = scheduler
        self.task_queue = task_queue
        self.task_name = task_name
        self.source = gobject.timeout_add(int(float(interval) * 1000.0 * TIME_FACTOR), self.exec_item, function, *args)
        self.complete = False
        self.scheduler.all_jobs.append(self)
        
    def exec_item(self, function, *args):
        try:
            logger.debug("Executing GTimer %s", str(self.task_name))
            ji = self.task_queue.run(self.stack, function, *args)
            logger.debug("Executed GTimer %s", str(self.task_name))
        finally:
            self.scheduler.all_jobs_lock.acquire()
            try:
                if self in self.scheduler.all_jobs:
                    self.scheduler.all_jobs.remove(self)
                self.complete = True
            finally:
                self.scheduler.all_jobs_lock.release()
                # Destroy the timeout, don't execute this function again.
                return False
        
    def is_complete(self):
        return self.complete
        
    def cancel(self, *args):
        self.scheduler.all_jobs_lock.acquire()
        try:
            if self in self.scheduler.all_jobs:
                self.scheduler.all_jobs.remove(self)
            # Check if callback function was executed, if yes this means that the timeout
            # was automatically destroyed since the callback function returns False.
            # Avoid thousands of warnings from source_remove().
            if not self.is_complete():
                gobject.source_remove(self.source)
            logger.debug("Cancelled GTimer %s", str(self.task_name))
        finally:
            self.scheduler.all_jobs_lock.release()
        
'''
Task scheduler. Tasks may be added to the queue to execute
after a specified interval. The timer is done by the gobject
event loop, which then executes the job on a different thread
'''

class JobScheduler():
    
    def __init__(self):
        self.queues = {}
        self.all_jobs = []
        self.all_jobs_lock = RLock()
        
    def print_all_jobs(self):
        print "Scheduled"
        print "------"
        for j in self.all_jobs:
            print "    %s - %s" % ( j.task_name, str(j.function))
        print
        print "Running"
        print "-------"
        for q in self.queues:
            self.queues[q].print_all_jobs()
        
    def schedule(self, name, interval, function, *args):
        return self.queue("default", name, interval, function, *args)
    
    def stop_all(self):
        logger.info("Stopping all queues")
        for queue_name in self.queues:
            self.queues[queue_name].stop()
    
    def clear_jobs(self, queue_name):
        if queue_name in self.queues:
            self.queues[queue_name].clear()
            
    def stop_queue(self, queue_name):
        if queue_name in self.queues:
            self.queues[queue_name].stop()
            del self.queues[queue_name]
    
    def execute(self, queue_name, name, function, *args):
        logger.debug("Executing on queue %s", queue_name)
        if not queue_name in self.queues:
            self.queues[queue_name] = JobQueue(name=queue_name)   
        self.queues[queue_name].run(self._get_stack(), function, *args)        
        
    def _get_stack(self):
        try: 1/0
        except:
            tb = sys.exc_info()[2]
            return traceback.extract_stack()[:-5]
    
    def queue(self, queue_name, name, interval, function, *args):
        if not hasattr(function, "__call__"):
            raise Exception("Not a function")
        logger.debug("Queueing %s on %s for execution in %f", name, queue_name, interval)
        if not queue_name in self.queues:
            self.queues[queue_name] = JobQueue(name=queue_name)
        
        if interval == 0:
            # Optimisation, if this is un-timed, avoid putting on main loop
            self.queues[queue_name].run(self._get_stack(), function, *args)
        else:
            timer = GTimer(self, self.queues[queue_name], name, interval, function, self._get_stack(), *args)
            logger.debug("Queued %s", name)
            return timer


class JobQueue():
    
    class JobItem():
        def __init__(self, stack, item, args = None):
            self.args = args
            self.item = item
            self.queued = time.time()
            self.started = None
            self.finished = None
            self.stack = stack
        
    def __init__(self,number_of_workers=1, name="JobQueue"):
        logger.debug("Creating job queue %s with %d workers", name, number_of_workers)
        self.work_queue = Queue.Queue()
        self.queued_jobs = []
        self.name = name
        self.stopping = False
        self.all_jobs_lock = threading.Lock()
        self.number_of_workers = number_of_workers
        self.threads = []
        for __ in range(number_of_workers):
            t = threading.Thread(target = self.worker)
            t.name = name
            t.setDaemon(True)
            t.start()
            self.threads.append(t)
            
    def print_all_jobs(self):
        print "Queue %s" % self.name
        for s in self.queued_jobs:
            print "     %s - %s" % (str(s.item), str(s.queued))
            
    def stop(self):
        logger.info("Stopping queue %s", self.name)
        self.stopping = True
        self.clear()
        for i in range(0, self.number_of_workers):
            self.work_queue.put(self.JobItem("Stopping", self._dummy))
        logger.info("Stopped queue %s", self.name)
        
    def _dummy(self):
        pass
            
    def clear(self):
        jobs = self.work_queue.qsize()
        if jobs > 0:
            logger.info("Clearing queue %s as it has %d jobs", self.name, jobs)
            try :
                while True:
                    item = self.work_queue.get_nowait()
                    logger.debug("Removed func = %s, args = %s, queued = %s, " \
                                 "started = %s, finished = %s",
                                 str(item.item),
                                 str(item.args),
                                 str(item.queued),
                                 str(item.started),
                                 str(item.finished))
                    if item in self.queued_jobs:
                        self.queued_jobs.remove(item)
            except Queue.Empty as e:
                logger.debug("The queue is already empty", exc_info = e)
                pass
            logger.info("Cleared queue %s", self.name)
            
    def run(self, stack, item, *args):
        if self.stopping:
            return
        if item == None:
            logger.warning("Attempt to run empty job.")
            traceback.print_stack()
            return
        self.all_jobs_lock.acquire()
        try :
            logger.debug("Queued task on %s", self.name)
            ji = self.JobItem(stack, item, args)
            self.queued_jobs.append(ji)
            self.work_queue.put(ji)
            jobs = self.work_queue.qsize()
            if jobs > 1:
                logger.debug("Queue %s filling, now at %d jobs.", self.name, jobs)
                
        finally :
            self.all_jobs_lock.release()
        return ji
            
    def worker(self):
        queue_names.queue_name = self.name
        while not self.stopping:
            item = self.work_queue.get()
            try:
                if item != None:
                    try:
                        logger.debug("Running task on %s", self.name)
                        item.started = time.time()
                        if item.args and len(item.args) > 0:
                            item.item(*item.args)
                        else:
                            item.item()
                        item.finished = time.time()
                        logger.debug("Ran task on %s", self.name)
                    finally:
                        if item in self.queued_jobs: 
                            self.queued_jobs.remove(item)
            except Exception as a:
                try:
                    logger.debug("Error on worker", exc_info = a)
                    logger.debug("Caused by job")
                    logger.debug("%s\n", item.stack)
                except Exception as e:
                    logger.debug("Could not log error on worker", exc_info = e)
                    pass
            self.work_queue.task_done()
            
        if logger:
            try:
                logger.info("Exited queue %s", self.name)
            except Exception as e:
                pass
 
