# Лабораторная работа 2. Потоки. Процессы. Асинхронность.

## Задача 1: Различия между threading, multiprocessing и async в Python

**Задача**: Напишите три различных программы на Python, использующие каждый из подходов: threading, multiprocessing и async. Каждая программа должна решать считать сумму всех чисел от 1 до 1000000000. Разделите вычисления на несколько параллельных задач для ускорения выполнения.

### threading

```
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
```

#### Результат работы кода:

![результат выполнения threading](https://i.ibb.co/7xp8m7t1/2025-09-11-21-23-26.png)

#### Вывод:

Плюсы:

* Легковесные (мало памяти)
* Быстрое создание/уничтожение
* Общая память (легко обмениваться данными)
* Хорошо для I/O-bound задач

Минусы:

* GIL ограничивает CPU-bound задачи
* Нет настоящего параллелизма на многоядерных CPU
* Сложная синхронизация при записи

Когда использовать?

* Много I/O операций (сеть, файлы, БД)
* GUI приложения (чтобы не зависал интерфейс)
* Веб-серверы (обработка запросов)
* Задачи с ожиданием

### multiprocessing

```
import multiprocessing
import time

def calculate_sum(start, end, result_queue):
    """Вычисляет сумму арифметической прогрессии"""
    n = end - start + 1
    partial_sum = n * (start + end) // 2
    result_queue.put(partial_sum)

def multiprocessing_sum(N, num_processes=4):
    chunk_size = N // num_processes
    processes = []
    result_queue = multiprocessing.Queue()

    start_time = time.time()

    for i in range(num_processes):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i != num_processes - 1 else N
        process = multiprocessing.Process(
            target=calculate_sum, 
            args=(start, end, result_queue)
        )
        processes.append(process)
        process.start()

    # Ждем завершения всех процессов
    for process in processes:
        process.join()

    # Собираем результаты из очереди
    total = 0
    for _ in range(num_processes):
        total += result_queue.get()

    end_time = time.time()
    
    print(f"Multiprocessing sum: {total}")
    print(f"Time: {end_time - start_time:.4f} seconds")
    print(f"Processes used: {num_processes}")
    return end_time - start_time

def verify_result(N):
    """Проверка результата"""
    expected = N * (N + 1) // 2
    print(f"Expected result: {expected}")
    return expected

if __name__ == "__main__":
    N = 1_000_000_000
    print(f"Calculating sum from 1 to {N:,}")
    
    expected = verify_result(N)
    
    times = {}
    for num_processes in [1, 2, 4, 8]:
        print(f"\n--- Using {num_processes} processes ---")
        duration = multiprocessing_sum(N, num_processes)
        times[num_processes] = duration
```

#### Результат работы кода:

![результат выполнения multiprocessing](https://i.ibb.co/TqDGhjJv/2025-09-11-21-34-43.png)

#### Вывод:

Плюсы:

* Настоящий параллелизм (использует все ядра CPU)
* Нет GIL ограничений
* Изоляция процессов (один упал - другие работают)
* Лучшая производительность для CPU-bound задач

Минусы:

* Больше потребление памяти
* Медленнее создание процессов
* Сложнее обмен данными (очереди, пайпы)

Когда использовать?

* Интенсивные вычисления (CPU-bound)
* Научные расчеты
* Обработка больших данных
* Параллельные алгоритмы

### async

```
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
```

#### Результат работы кода:

![результат выполнения threading](https://i.ibb.co/3mCsnSp3/2025-09-11-22-05-30.png)

#### Вывод:

Плюсы:

* Очень легковесные (корутины)
* Отлично для I/O-bound
* Эффективное использование CPU

Минусы:

* Не подходит для CPU-bound
* Сложность с блокирующими операциями
* Кривая обучения

Когда использовать?

* Много I/O операций (сеть, БД, файлы)
* Важна эффективность использования ресурсов
* Работаете с веб-сокетами или real-time данными

### Сравнение

| Method | Time for 1M (sec) |
|-------------|-------------|
| threading | 0.0001 |
| multiprocessing | 0.0486 |
| async | 0.0002 |

Для CPU-задач (вычисления, математика) Multiprocessing показывает наилучший результат.

При работе над I/O-задачами (сеть, файлы) Threading или Async были бы лучше. Но даже между ними борьба. Async лучше Threading для высоконагруженных I/O-систем (веб-серверы), хотя Threading и проще в использовании, но не дает ускорения на CPU