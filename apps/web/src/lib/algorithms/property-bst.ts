/**
 * Binary Search Tree optimized for range queries on property values
 * Provides O(log n) search, insert, and delete operations
 */

export interface PropertyNode {
  id: string;
  value: number; // Can be price, sqft, year, etc.
  data: any;
  left: PropertyNode | null;
  right: PropertyNode | null;
  height: number; // For AVL balancing
}

/**
 * AVL Tree (self-balancing BST) for property range queries
 */
export class PropertyBST {
  private root: PropertyNode | null = null;
  private nodeCount = 0;
  private valueField: string;

  constructor(valueField = 'price') {
    this.valueField = valueField;
  }

  /**
   * Insert a property into the tree
   */
  insert(id: string, value: number, data: any): void {
    this.root = this.insertNode(this.root, id, value, data);
    this.nodeCount++;
  }

  private insertNode(node: PropertyNode | null, id: string, value: number, data: any): PropertyNode {
    // Base case: create new node
    if (!node) {
      return {
        id,
        value,
        data,
        left: null,
        right: null,
        height: 1
      };
    }

    // Insert recursively
    if (value < node.value) {
      node.left = this.insertNode(node.left, id, value, data);
    } else if (value > node.value) {
      node.right = this.insertNode(node.right, id, value, data);
    } else {
      // Equal values - can store multiple properties with same value
      // For simplicity, update the data
      node.data = data;
      return node;
    }

    // Update height
    node.height = 1 + Math.max(this.getHeight(node.left), this.getHeight(node.right));

    // Rebalance if needed (AVL property)
    return this.rebalance(node);
  }

  /**
   * Find all properties within a value range
   * @param min Minimum value (inclusive)
   * @param max Maximum value (inclusive)
   * @returns Array of properties in range
   */
  findInRange(min: number, max: number): Array<{ id: string; value: number; data: any }> {
    const result: Array<{ id: string; value: number; data: any }> = [];
    this.inOrderTraversalRange(this.root, min, max, result);
    return result;
  }

  private inOrderTraversalRange(
    node: PropertyNode | null,
    min: number,
    max: number,
    result: Array<{ id: string; value: number; data: any }>
  ): void {
    if (!node) return;

    // Optimize traversal by pruning branches
    if (node.value > min) {
      this.inOrderTraversalRange(node.left, min, max, result);
    }

    if (node.value >= min && node.value <= max) {
      result.push({
        id: node.id,
        value: node.value,
        data: node.data
      });
    }

    if (node.value < max) {
      this.inOrderTraversalRange(node.right, min, max, result);
    }
  }

  /**
   * Count properties within a range
   * More efficient than findInRange when only count is needed
   */
  countInRange(min: number, max: number): number {
    return this.countRange(this.root, min, max);
  }

  private countRange(node: PropertyNode | null, min: number, max: number): number {
    if (!node) return 0;

    let count = 0;

    if (node.value >= min && node.value <= max) {
      count = 1;
    }

    if (node.value > min) {
      count += this.countRange(node.left, min, max);
    }

    if (node.value < max) {
      count += this.countRange(node.right, min, max);
    }

    return count;
  }

  /**
   * Find the property with minimum value
   */
  findMin(): { id: string; value: number; data: any } | null {
    if (!this.root) return null;
    
    let current = this.root;
    while (current.left) {
      current = current.left;
    }
    
    return {
      id: current.id,
      value: current.value,
      data: current.data
    };
  }

  /**
   * Find the property with maximum value
   */
  findMax(): { id: string; value: number; data: any } | null {
    if (!this.root) return null;
    
    let current = this.root;
    while (current.right) {
      current = current.right;
    }
    
    return {
      id: current.id,
      value: current.value,
      data: current.data
    };
  }

  /**
   * Find properties with value greater than threshold
   */
  findGreaterThan(threshold: number, limit?: number): Array<{ id: string; value: number; data: any }> {
    const result: Array<{ id: string; value: number; data: any }> = [];
    this.inOrderTraversalGreater(this.root, threshold, result, limit);
    return result;
  }

  private inOrderTraversalGreater(
    node: PropertyNode | null,
    threshold: number,
    result: Array<{ id: string; value: number; data: any }>,
    limit?: number
  ): void {
    if (!node || (limit && result.length >= limit)) return;

    // Go left first (smaller values)
    this.inOrderTraversalGreater(node.left, threshold, result, limit);

    // Process current node
    if (node.value > threshold && (!limit || result.length < limit)) {
      result.push({
        id: node.id,
        value: node.value,
        data: node.data
      });
    }

    // Go right (larger values)
    if (node.value > threshold || !limit || result.length < limit) {
      this.inOrderTraversalGreater(node.right, threshold, result, limit);
    }
  }

  /**
   * Find properties with value less than threshold
   */
  findLessThan(threshold: number, limit?: number): Array<{ id: string; value: number; data: any }> {
    const result: Array<{ id: string; value: number; data: any }> = [];
    this.inOrderTraversalLess(this.root, threshold, result, limit);
    return result;
  }

  private inOrderTraversalLess(
    node: PropertyNode | null,
    threshold: number,
    result: Array<{ id: string; value: number; data: any }>,
    limit?: number
  ): void {
    if (!node || (limit && result.length >= limit)) return;

    // Process larger values first (go right)
    if (node.value < threshold) {
      this.inOrderTraversalLess(node.right, threshold, result, limit);
    }

    // Process current node
    if (node.value < threshold && (!limit || result.length < limit)) {
      result.push({
        id: node.id,
        value: node.value,
        data: node.data
      });
    }

    // Go left (smaller values)
    this.inOrderTraversalLess(node.left, threshold, result, limit);
  }

  /**
   * Get percentile value (e.g., median = 50th percentile)
   */
  getPercentile(percentile: number): number | null {
    if (!this.root || percentile < 0 || percentile > 100) return null;

    const allValues: number[] = [];
    this.collectAllValues(this.root, allValues);
    
    if (allValues.length === 0) return null;
    
    const index = Math.floor((percentile / 100) * (allValues.length - 1));
    return allValues[index];
  }

  private collectAllValues(node: PropertyNode | null, values: number[]): void {
    if (!node) return;
    
    this.collectAllValues(node.left, values);
    values.push(node.value);
    this.collectAllValues(node.right, values);
  }

  /**
   * Rebalance the tree (AVL rotation)
   */
  private rebalance(node: PropertyNode): PropertyNode {
    const balance = this.getBalance(node);

    // Left-heavy
    if (balance > 1) {
      if (this.getBalance(node.left) < 0) {
        node.left = this.rotateLeft(node.left!);
      }
      return this.rotateRight(node);
    }

    // Right-heavy
    if (balance < -1) {
      if (this.getBalance(node.right) > 0) {
        node.right = this.rotateRight(node.right!);
      }
      return this.rotateLeft(node);
    }

    return node;
  }

  private rotateRight(y: PropertyNode): PropertyNode {
    const x = y.left!;
    const T2 = x.right;

    x.right = y;
    y.left = T2;

    y.height = 1 + Math.max(this.getHeight(y.left), this.getHeight(y.right));
    x.height = 1 + Math.max(this.getHeight(x.left), this.getHeight(x.right));

    return x;
  }

  private rotateLeft(x: PropertyNode): PropertyNode {
    const y = x.right!;
    const T2 = y.left;

    y.left = x;
    x.right = T2;

    x.height = 1 + Math.max(this.getHeight(x.left), this.getHeight(x.right));
    y.height = 1 + Math.max(this.getHeight(y.left), this.getHeight(y.right));

    return y;
  }

  private getHeight(node: PropertyNode | null): number {
    return node ? node.height : 0;
  }

  private getBalance(node: PropertyNode | null): number {
    return node ? this.getHeight(node.left) - this.getHeight(node.right) : 0;
  }

  /**
   * Get tree statistics
   */
  getStats(): {
    count: number;
    min: number | null;
    max: number | null;
    median: number | null;
    height: number;
  } {
    return {
      count: this.nodeCount,
      min: this.findMin()?.value ?? null,
      max: this.findMax()?.value ?? null,
      median: this.getPercentile(50),
      height: this.getHeight(this.root)
    };
  }

  /**
   * Clear the tree
   */
  clear(): void {
    this.root = null;
    this.nodeCount = 0;
  }
}

/**
 * Multi-dimensional BST for complex queries
 * e.g., find properties with price between X-Y AND sqft between A-B
 */
export class MultiPropertyBST {
  private trees: Map<string, PropertyBST>;

  constructor() {
    this.trees = new Map();
  }

  /**
   * Add a tree for a specific property field
   */
  addIndex(field: string): void {
    if (!this.trees.has(field)) {
      this.trees.set(field, new PropertyBST(field));
    }
  }

  /**
   * Insert property into all relevant trees
   */
  insert(property: any): void {
    const id = property.id || property.parcel_id;
    
    // Insert into each indexed field
    this.trees.forEach((tree, field) => {
      const value = this.extractValue(property, field);
      if (value !== null && !isNaN(value)) {
        tree.insert(id, value, property);
      }
    });
  }

  /**
   * Find properties matching multiple range criteria
   */
  findMultiRange(criteria: Array<{ field: string; min: number; max: number }>): any[] {
    if (criteria.length === 0) return [];

    // Get results from first criterion
    const firstCriterion = criteria[0];
    const firstTree = this.trees.get(firstCriterion.field);
    if (!firstTree) return [];

    let results = firstTree.findInRange(firstCriterion.min, firstCriterion.max);
    const resultIds = new Set(results.map(r => r.id));

    // Intersect with remaining criteria
    for (let i = 1; i < criteria.length; i++) {
      const criterion = criteria[i];
      const tree = this.trees.get(criterion.field);
      if (!tree) return [];

      const rangeResults = tree.findInRange(criterion.min, criterion.max);
      const rangeIds = new Set(rangeResults.map(r => r.id));

      // Keep only IDs present in both sets
      const intersection = new Set();
      resultIds.forEach(id => {
        if (rangeIds.has(id)) {
          intersection.add(id);
        }
      });

      // Filter results
      results = results.filter(r => intersection.has(r.id));
      resultIds.clear();
      intersection.forEach(id => resultIds.add(id));
    }

    return results.map(r => r.data);
  }

  /**
   * Extract numeric value from property object
   */
  private extractValue(property: any, field: string): number | null {
    const value = property[field];
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      return isNaN(parsed) ? null : parsed;
    }
    return null;
  }

  /**
   * Clear all trees
   */
  clear(): void {
    this.trees.forEach(tree => tree.clear());
  }
}