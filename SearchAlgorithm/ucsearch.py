import heapq

def ucs(graph, start, target):
    # Priority Queue menyimpan tuple (biaya_kumulatif, simpul)
    pq = [(0, start)]
    visited = set()
    
    while pq:
        cost, node = heapq.heappop(pq)
        
        if node == target:
            return cost
            
        if node in visited:
            continue
            
        visited.add(node)
        
        for neighbor, weight in graph[node]:
            if neighbor not in visited:
                heapq.heappush(pq, (cost + weight, neighbor))
                
    return float('inf') # Jika tidak ada jalur

if __name__ == "__main__":
    # Graf berbobot: node: [(neighbor, bobot)]
    graph = {
        0: [(1, 2), (2, 5)],
        1: [(0, 2), (2, 1), (3, 4)],
        2: [(0, 5), (1, 1), (4, 3)],
        3: [(1, 4), (4, 1)],
        4: [(2, 3), (3, 1)]
    }
    cost = ucs(graph, 0, 4)
    print(f"UCS: Biaya minimum dari 0 ke 4 adalah {cost}")
    