from concurrent.futures import ThreadPoolExecutor, as_completed, wait
  

class Concurrent(object):
        """Simple concurrent task helper.
        """

        def __init__(self):
                self.tasks = []

        def add(self, task, *args, **kwargs):
                """Add a new task.

                Args:
                        task (fn): function ref
                        args (args): funtion params
                        kwargs (kwargs): funtion keyword params
                """
                self.tasks.append((task, args, kwargs))
                return self

        def run(self, threads=None):
                """Run all registered tasks concurrently.

                Args:
                        threads (int)
                """
                if len(self.tasks) == 0:
                        return

                thread_count = threads if threads is not None else len(self.tasks)
                pool = ThreadPoolExecutor(thread_count)
                futures = []
                for task, args, kwargs in self.tasks:
                        futures.append(pool.submit(task, *args, **kwargs))

                wait(futures)

                for future in futures:
                        future.result()

                # a task set should only run once
                self.tasks = []
