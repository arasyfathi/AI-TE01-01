def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
            
    return -1

if __name__ == "__main__":
    arr = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91] # Data wajib terurut
    target = 23
    result = binary_search(arr, target)
    print(f"Binary Search: Elemen ditemukan di indeks {result}")