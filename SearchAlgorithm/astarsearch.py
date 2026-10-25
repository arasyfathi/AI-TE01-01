import heapq

def a_star(graph, heuristic, start, target):
    # Priority Queue menyimpan tuple (f_cost, g_cost, node)
    pq = [(heuristic[start], 0, start)]
    visited = set()
    
    while pq:
        f, g, node = heapq.heappop(pq)
        
        if node == target:
            return g # Mengembalikan biaya riil (g)
            
        if node in visited:
            continue
            
        visited.add(node)
        
        for neighbor, weight in graph[node]:
            if neighbor not in visited:
                new_g = g + weight
                new_f = new_g + heuristic[neighbor]
                heapq.heappush(pq, (new_f, new_g, neighbor))
                
    return float('inf')

if __name__ == "__main__":
    graph = {
        0: [(1, 2), (2, 5)],
        1: [(2, 1), (3, 4)],
        2: [(4, 3)],
        3: [(4, 1)],
        4: []
    }
    # Nilai heuristik (h) dari tiap simpul menuju simpul target (4)
    heuristic = {0: 4, 1: 2, 2: 3, 3: 1, 4: 0}
    
    cost = a_star(graph, heuristic, 0, 4)
    print(f"A*: Biaya minimum menuju 4 adalah {cost}")