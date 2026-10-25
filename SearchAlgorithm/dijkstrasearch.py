import heapq

def dijkstra(graph, start):
    # Inisialisasi jarak ke semua simpul dengan infinity
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    
    pq = [(0, start)]
    
    while pq:
        current_dist, node = heapq.heappop(pq)
        
        # Jika jarak yang diproses lebih besar dari yang dicatat, abaikan
        if current_dist > distances[node]:
            continue
            
        for neighbor, weight in graph[node]:
            distance = current_dist + weight
            
            # Jika menemukan jalur yang lebih pendek, perbarui jarak
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
                
    return distances

if __name__ == "__main__":
    graph = {
        0: [(1, 10), (3, 5)],
        1: [(2, 1), (3, 2)],
        2: [(4, 4)],
        3: [(1, 3), (2, 9), (4, 2)],
        4: [(0, 7), (2, 6)]
    }
    
    distances = dijkstra(graph, 0)
    print(f"Dijkstra: Jarak minimum dari node 0:")
    for node, dist in distances.items():
        print(f"Ke node {node} = {dist}")