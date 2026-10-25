def dfs(graph, node, visited=None):
    if visited is None:
        visited = set()
        print("DFS Traversal:", end=" ")
        
    visited.add(node)
    print(node, end=" ")
    
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)

if __name__ == "__main__":
    graph = {
        0: [1, 2],
        1: [0, 3, 4],
        2: [0],
        3: [1],
        4: [1]
    }
    dfs(graph, 0)
    print()