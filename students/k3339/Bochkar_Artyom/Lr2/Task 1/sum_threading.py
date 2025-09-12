import threading
import time


def calculate_sum(start, end, result, index):
  """Вычисляет сумму арифметической прогрессии (формула Гаусса)"""
  n = end - start + 1
  result[index] = n * (start + end) // 2


def threading_sum(N, num_threads=4):
  chunk_size = N // num_threads
  threads = []
  results = [0] * num_threads

  start_time = time.time()

  for i in range(num_threads):
    start = i * chunk_size + 1
    end = (i + 1) * chunk_size if i != num_threads - 1 else N
    thread = threading.Thread(target=calculate_sum, args=(start, end, results, i))
    threads.append(thread)
    thread.start()

  for thread in threads:
    thread.join()

  total = sum(results)
  end_time = time.time()

  print(f"Threading sum: {total}")
  print(f"Time: {end_time - start_time:.4f} seconds")
  print(f"Threads used: {num_threads}")


def verify_result(N):
  """Проверка результата с помощью математической формулы"""
  expected = N * (N + 1) // 2
  print(f"Expected result: {expected}")
  return expected


if __name__ == "__main__":
  N = 1_000_000_000
  print(f"Calculating sum from 1 to {N:,}")

  # Проверка
  expected = verify_result(N)

  # Запуск с разным количеством потоков для сравнения
  for num_threads in [1, 2, 4, 8]:
    print(f"\n--- Using {num_threads} threads ---")
    threading_sum(N, num_threads)