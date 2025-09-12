import asyncio
import time


async def calculate_sum_async(start, end):
  """Асинхронно вычисляет сумму арифметической прогрессии"""
  n = end - start + 1
  # Имитируем асинхронную операцию (хотя вычисления синхронные)
  await asyncio.sleep(0.000001)  # Минимальная пауза для демонстрации
  return n * (start + end) // 2


async def async_sum(N, num_tasks=4):
  """Асинхронная версия вычисления суммы"""
  chunk_size = N // num_tasks
  tasks = []

  start_time = time.time()

  # Создаем задачи
  for i in range(num_tasks):
    start = i * chunk_size + 1
    end = (i + 1) * chunk_size if i != num_tasks - 1 else N
    task = asyncio.create_task(calculate_sum_async(start, end))
    tasks.append(task)

  # Запускаем все задачи параллельно
  results = await asyncio.gather(*tasks)
  total = sum(results)

  end_time = time.time()

  print(f"Async sum: {total}")
  print(f"Time: {end_time - start_time:.4f} seconds")
  print(f"Tasks used: {num_tasks}")
  return end_time - start_time


def verify_result(N):
  """Проверка результата"""
  expected = N * (N + 1) // 2
  print(f"Expected result: {expected}")
  return expected


async def main():
  N = 1_000_000_000
  print(f"Calculating sum from 1 to {N:,}")

  expected = verify_result(N)

  times_async = {}
  for num_tasks in [1, 2, 4, 8]:
    print(f"\n--- Using {num_tasks} tasks ---")
    duration = await async_sum(N, num_tasks)
    times_async[num_tasks] = duration

  return times_async


if __name__ == "__main__":
  times = asyncio.run(main())