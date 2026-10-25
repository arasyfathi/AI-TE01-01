def dls(graph, node, target, limit):
    if node == target:
        return True
    if limit <= 0:
        return False
        
    for neighbor in graph[node]:
        if dls(graph, neighbor, target, limit - 1):
            return True
            
    return False

def iddfs(graph, start, target, max_depth):
    for depth in range(max_depth + 1):
        if dls(graph, start, target, depth):
            print(f"IDDFS: Target {target} ditemukan pada kedalaman {depth}")
            return True
    print("IDDFS: Target tidak ditemukan dalam batas kedalaman")
    return False

if __name__ == "__main__":
    graph = {
        0: [1, 2],
        1: [3, 4],
        2: [],
        3: [],
        4: []
    }
    iddfs(graph, 0, 4, 3)