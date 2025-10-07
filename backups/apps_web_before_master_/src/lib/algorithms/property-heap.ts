/**
 * Min/Max Heap implementation for efficient top-N property scoring
 * Provides O(log n) insertion and O(1) access to best/worst properties
 */

export interface ScoredProperty {
  id: string;
  score: number;
  data: any;
}

export class PropertyHeap {
  private heap: ScoredProperty[];
  private compareFn: (a: ScoredProperty, b: ScoredProperty) => number;
  private idMap: Map<string, number>; // Map ID to heap index for O(1) lookups

  constructor(isMaxHeap = true) {
    this.heap = [];
    this.idMap = new Map();
    
    // Max heap: parent >= children, Min heap: parent <= children
    this.compareFn = isMaxHeap
      ? (a, b) => b.score - a.score  // Max heap
      : (a, b) => a.score - b.score; // Min heap
  }

  /**
   * Insert a property with its score
   */
  insert(property: ScoredProperty): void {
    // Remove if already exists (update score)
    if (this.idMap.has(property.id)) {
      this.remove(property.id);
    }

    this.heap.push(property);
    const index = this.heap.length - 1;
    this.idMap.set(property.id, index);
    this.bubbleUp(index);
  }

  /**
   * Batch insert multiple properties
   */
  batchInsert(properties: ScoredProperty[]): void {
    properties.forEach(prop => this.insert(prop));
  }

  /**
   * Get the top property without removing it
   */
  peek(): ScoredProperty | null {
    return this.heap.length > 0 ? this.heap[0] : null;
  }

  /**
   * Extract the top property
   */
  extract(): ScoredProperty | null {
    if (this.heap.length === 0) return null;
    if (this.heap.length === 1) {
      const property = this.heap.pop()!;
      this.idMap.delete(property.id);
      return property;
    }

    const root = this.heap[0];
    this.heap[0] = this.heap.pop()!;
    this.idMap.delete(root.id);
    this.idMap.set(this.heap[0].id, 0);
    this.bubbleDown(0);
    
    return root;
  }

  /**
   * Get top N properties without removing them
   */
  getTopN(n: number): ScoredProperty[] {
    const result: ScoredProperty[] = [];
    const tempHeap = [...this.heap];
    const tempMap = new Map(this.idMap);

    for (let i = 0; i < Math.min(n, this.heap.length); i++) {
      const property = this.extract();
      if (property) result.push(property);
    }

    // Restore heap
    this.heap = tempHeap;
    this.idMap = tempMap;

    return result;
  }

  /**
   * Remove a property by ID
   */
  remove(id: string): boolean {
    if (!this.idMap.has(id)) return false;

    const index = this.idMap.get(id)!;
    const property = this.heap[index];

    if (index === this.heap.length - 1) {
      this.heap.pop();
      this.idMap.delete(id);
      return true;
    }

    this.heap[index] = this.heap.pop()!;
    this.idMap.delete(id);
    this.idMap.set(this.heap[index].id, index);

    // Restore heap property
    this.bubbleUp(index);
    this.bubbleDown(index);

    return true;
  }

  /**
   * Update score for a property
   */
  updateScore(id: string, newScore: number): boolean {
    if (!this.idMap.has(id)) return false;

    const index = this.idMap.get(id)!;
    const oldScore = this.heap[index].score;
    this.heap[index].score = newScore;

    // Restore heap property based on score change
    if (newScore > oldScore) {
      this.bubbleUp(index);
    } else if (newScore < oldScore) {
      this.bubbleDown(index);
    }

    return true;
  }

  /**
   * Bubble up to maintain heap property
   */
  private bubbleUp(index: number): void {
    while (index > 0) {
      const parentIndex = Math.floor((index - 1) / 2);
      
      if (this.compareFn(this.heap[parentIndex], this.heap[index]) <= 0) {
        break;
      }

      this.swap(index, parentIndex);
      index = parentIndex;
    }
  }

  /**
   * Bubble down to maintain heap property
   */
  private bubbleDown(index: number): void {
    while (true) {
      const leftChild = 2 * index + 1;
      const rightChild = 2 * index + 2;
      let targetIndex = index;

      if (
        leftChild < this.heap.length &&
        this.compareFn(this.heap[leftChild], this.heap[targetIndex]) < 0
      ) {
        targetIndex = leftChild;
      }

      if (
        rightChild < this.heap.length &&
        this.compareFn(this.heap[rightChild], this.heap[targetIndex]) < 0
      ) {
        targetIndex = rightChild;
      }

      if (targetIndex === index) break;

      this.swap(index, targetIndex);
      index = targetIndex;
    }
  }

  /**
   * Swap two elements in the heap
   */
  private swap(i: number, j: number): void {
    [this.heap[i], this.heap[j]] = [this.heap[j], this.heap[i]];
    this.idMap.set(this.heap[i].id, i);
    this.idMap.set(this.heap[j].id, j);
  }

  /**
   * Get heap size
   */
  size(): number {
    return this.heap.length;
  }

  /**
   * Check if heap is empty
   */
  isEmpty(): boolean {
    return this.heap.length === 0;
  }

  /**
   * Clear the heap
   */
  clear(): void {
    this.heap = [];
    this.idMap.clear();
  }

  /**
   * Get all properties sorted by score
   */
  toSortedArray(): ScoredProperty[] {
    const result: ScoredProperty[] = [];
    const tempHeap = [...this.heap];
    const tempMap = new Map(this.idMap);

    while (!this.isEmpty()) {
      const property = this.extract();
      if (property) result.push(property);
    }

    // Restore heap
    this.heap = tempHeap;
    this.idMap = tempMap;

    return result;
  }

  /**
   * Find properties within a score range
   */
  findInRange(minScore: number, maxScore: number): ScoredProperty[] {
    return this.heap.filter(p => p.score >= minScore && p.score <= maxScore);
  }
}

/**
 * Specialized heap for maintaining top K properties efficiently
 * Uses a min heap of size K to track the K highest scoring properties
 */
export class TopKPropertyHeap {
  private heap: PropertyHeap;
  private k: number;

  constructor(k: number) {
    this.k = k;
    this.heap = new PropertyHeap(false); // Min heap
  }

  /**
   * Add a property - only keeps if in top K
   */
  add(property: ScoredProperty): boolean {
    if (this.heap.size() < this.k) {
      this.heap.insert(property);
      return true;
    }

    const minProperty = this.heap.peek();
    if (minProperty && property.score > minProperty.score) {
      this.heap.extract();
      this.heap.insert(property);
      return true;
    }

    return false;
  }

  /**
   * Get the top K properties sorted by score
   */
  getTopK(): ScoredProperty[] {
    return this.heap.toSortedArray().reverse(); // Reverse since we use min heap
  }

  /**
   * Get the minimum score needed to be in top K
   */
  getThresholdScore(): number {
    const minProperty = this.heap.peek();
    return minProperty ? minProperty.score : 0;
  }

  clear(): void {
    this.heap.clear();
  }
}