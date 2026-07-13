"""
algorithms.py — Generator-based sorting algorithms for visualization.

Each algorithm is a generator that yields tuples describing the operation:
    ("compare", i, j)    — comparing indices i and j
    ("swap", i, j)       — swapping indices i and j
    ("set", i, value)    — setting index i to value
    ("access", i)        — accessing index i (read)
    ("done",)            — sorting complete
"""


def bubble_sort(arr: list[int]):
    """Bubble Sort — O(n²) average and worst case."""
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            yield ("compare", j, j + 1)
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                yield ("swap", j, j + 1)
                swapped = True
        if not swapped:
            break
    yield ("done",)


def selection_sort(arr: list[int]):
    """Selection Sort — O(n²) average and worst case."""
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            yield ("compare", min_idx, j)
            if arr[j] < arr[min_idx]:
                min_idx = j
        if min_idx != i:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            yield ("swap", i, min_idx)
    yield ("done",)


def insertion_sort(arr: list[int]):
    """Insertion Sort — O(n²) average and worst case, O(n) best case."""
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        yield ("access", i)
        j = i - 1
        while j >= 0:
            yield ("compare", j, i)
            if arr[j] <= key:
                break
            arr[j + 1] = arr[j]
            yield ("set", j + 1, arr[j + 1])
            j -= 1
        arr[j + 1] = key
        yield ("set", j + 1, key)
    yield ("done",)


def merge_sort(arr: list[int]):
    """Merge Sort — O(n log n) all cases. Uses auxiliary array for merging."""
    yield from _merge_sort_recursive(arr, 0, len(arr) - 1)
    yield ("done",)


def _merge_sort_recursive(arr: list[int], left: int, right: int):
    if left < right:
        mid = (left + right) // 2
        yield from _merge_sort_recursive(arr, left, mid)
        yield from _merge_sort_recursive(arr, mid + 1, right)
        yield from _merge(arr, left, mid, right)


def _merge(arr: list[int], left: int, mid: int, right: int):
    """Merge two sorted sub-arrays."""
    left_copy = arr[left:mid + 1]
    right_copy = arr[mid + 1:right + 1]

    i = 0
    j = 0
    k = left

    while i < len(left_copy) and j < len(right_copy):
        yield ("compare", left + i, mid + 1 + j)
        if left_copy[i] <= right_copy[j]:
            arr[k] = left_copy[i]
            yield ("set", k, left_copy[i])
            i += 1
        else:
            arr[k] = right_copy[j]
            yield ("set", k, right_copy[j])
            j += 1
        k += 1

    while i < len(left_copy):
        arr[k] = left_copy[i]
        yield ("set", k, left_copy[i])
        i += 1
        k += 1

    while j < len(right_copy):
        arr[k] = right_copy[j]
        yield ("set", k, right_copy[j])
        j += 1
        k += 1


def quick_sort(arr: list[int]):
    """Quick Sort — O(n log n) average, O(n²) worst case."""
    yield from _quick_sort_recursive(arr, 0, len(arr) - 1)
    yield ("done",)


def _quick_sort_recursive(arr: list[int], low: int, high: int):
    if low < high:
        pivot_idx = yield from _partition(arr, low, high)
        yield from _quick_sort_recursive(arr, low, pivot_idx - 1)
        yield from _quick_sort_recursive(arr, pivot_idx + 1, high)


def _partition(arr: list[int], low: int, high: int):
    """Lomuto partition scheme with last element as pivot."""
    pivot = arr[high]
    yield ("access", high)
    i = low - 1

    for j in range(low, high):
        yield ("compare", j, high)
        if arr[j] <= pivot:
            i += 1
            if i != j:
                arr[i], arr[j] = arr[j], arr[i]
                yield ("swap", i, j)

    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    yield ("swap", i + 1, high)
    return i + 1


# Algorithm registry
ALGORITHMS = {
    "Bubble Sort": bubble_sort,
    "Selection Sort": selection_sort,
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort,
}

ALGORITHM_NAMES = list(ALGORITHMS.keys())
