import time
import threading

def cpu_burner(thread_id):
    start_time = time.time()
    duration = 180  # 3 minutes
    iteration = 0
    print(f"Thread {thread_id} started at {time.ctime()}")
    while time.time() - start_time < duration:
        result = 1
        for i in range(1, 1000):
            result *= i
        if iteration % 1000 == 0:
            print(f"Thread {thread_id} - Iteration {iteration} at {time.ctime()}, result: {result}")
        iteration += 1
    print(f"Thread {thread_id} finished at {time.ctime()}, total iterations: {iteration}")

# Log container start time
print(f"Starting CPU stress test at {time.ctime()}")

# Launch 2 threads to simulate load (even on 1 vCPU this creates contention)
threads = []
for i in range(2):
    t = threading.Thread(target=cpu_burner, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print(f"CPU stress test completed at {time.ctime()}")
