#!/usr/bin/env python3
# ============================================================
#   RUN ALL SEARCH ALGORITHMS - Demo Runner
# ============================================================

from collections import deque
import heapq
import sys

def header(title):
    print("\n" + "="*55)
    print(f"  {title}")
    print("="*55)

def result(msg):
    print(f"  >> {msg}")

# ============================================================
# 1. LINEAR SEARCH
# ============================================================
header("1. LINEAR SEARCH")

def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

arr = [10, 25, 3, 47, 8, 99, 56]
target = 47
idx = linear_search(arr, target)
print(f"  Array  : {arr}")
print(f"  Target : {target}")
result(f"Ditemukan di index: {idx}" if idx != -1 else "Tidak ditemukan")

target2 = 100
idx2 = linear_search(arr, target2)
print(f"  Target : {target2}")
result(f"Ditemukan di index: {idx2}" if idx2 != -1 else "Tidak ditemukan")

# ============================================================
# 2. BINARY SEARCH
# ============================================================
header("2. BINARY SEARCH")

def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

sorted_arr = [3, 8, 10, 25, 47, 56, 99]
target = 56
idx = binary_search(sorted_arr, target)
print(f"  Array  : {sorted_arr} (sudah diurutkan)")
print(f"  Target : {target}")
result(f"Ditemukan di index: {idx}" if idx != -1 else "Tidak ditemukan")

target2 = 15
idx2 = binary_search(sorted_arr, target2)
print(f"  Target : {target2}")
result(f"Ditemukan di index: {idx2}" if idx2 != -1 else "Tidak ditemukan")

# ============================================================
# 3. BREADTH FIRST SEARCH (BFS)
# ============================================================
header("3. BREADTH FIRST SEARCH (BFS)")

def bfs(graph, start):
    queue = deque([start])
    visited = []
    visited_set = set()

    while queue:
        vertex = queue.popleft()
        if vertex not in visited_set:
            visited_set.add(vertex)
            visited.append(vertex)
            for neighbor in graph[vertex]:
                if neighbor not in visited_set:
                    queue.append(neighbor)
    return visited

graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E'],
}
print(f"  Graph  : {graph}")
print(f"  Start  : A")
urutan = bfs(graph, 'A')
result(f"Urutan kunjungan: {' -> '.join(urutan)}")

# ============================================================
# 4. DEPTH FIRST SEARCH (DFS)
# ============================================================
header("4. DEPTH FIRST SEARCH (DFS)")

def dfs(graph, start):
    stack = [start]
    visited = []
    visited_set = set()

    while stack:
        vertex = stack.pop()
        if vertex not in visited_set:
            visited_set.add(vertex)
            visited.append(vertex)
            for neighbor in reversed(graph[vertex]):
                if neighbor not in visited_set:
                    stack.append(neighbor)
    return visited

print(f"  Graph  : {graph}")
print(f"  Start  : A")
urutan = dfs(graph, 'A')
result(f"Urutan kunjungan: {' -> '.join(urutan)}")

# ============================================================
# 5. DIJKSTRA'S ALGORITHM
# ============================================================
header("5. DIJKSTRA'S ALGORITHM")

def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    priority_queue = [(0, start)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        if current_distance > distances[current_node]:
            continue
        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(priority_queue, (distance, neighbor))
    return distances

weighted_graph = {
    'A': {'B': 4, 'C': 2},
    'B': {'A': 4, 'C': 1, 'D': 5},
    'C': {'A': 2, 'B': 1, 'D': 8, 'E': 10},
    'D': {'B': 5, 'C': 8, 'E': 2},
    'E': {'C': 10, 'D': 2},
}
print(f"  Start  : A")
distances = dijkstra(weighted_graph, 'A')
result("Jarak terpendek dari A ke semua node:")
for node, dist in sorted(distances.items()):
    print(f"     A -> {node} : {dist}")

# ============================================================
# 6. UNIFORM COST SEARCH (UCS)
# ============================================================
header("6. UNIFORM COST SEARCH (UCS)")

def ucs(graph, start, goal):
    priority_queue = [(0, start, [start])]
    visited = set()

    while priority_queue:
        cost, node, path = heapq.heappop(priority_queue)
        if node in visited:
            continue
        visited.add(node)
        if node == goal:
            return cost, path
        for neighbor, weight in graph[node].items():
            if neighbor not in visited:
                heapq.heappush(priority_queue, (cost + weight, neighbor, path + [neighbor]))
    return float('inf'), []

cost, path = ucs(weighted_graph, 'A', 'E')
print(f"  Start  : A  |  Goal : E")
result(f"Path terpendek: {' -> '.join(path)}")
result(f"Total cost    : {cost}")

# ============================================================
# SELESAI
# ============================================================
print("\n" + "="*55)
print("  SEMUA ALGORITMA BERHASIL DIJALANKAN!")
print("="*55 + "\n")
