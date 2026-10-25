from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    
    print("BFS Traversal:", end=" ")
    while queue:
        curr = queue.popleft()
        print(curr, end=" ")
        
        for neighbor in graph[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    print()

if __name__ == "__main__":
    # Representasi graf menggunakan Adjacency List
    graph = {
        0: [1, 2],
        1: [0, 3, 4],
        2: [0],
        3: [1],
        4: [1]
    }
    bfs(graph, 0)