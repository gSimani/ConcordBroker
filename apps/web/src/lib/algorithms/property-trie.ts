/**
 * Trie data structure optimized for property address autocomplete
 * Provides O(k) lookup where k is the length of the prefix
 */

interface TrieNode {
  children: Map<string, TrieNode>;
  isEndOfWord: boolean;
  suggestions: string[]; // Store top suggestions at each node
  count: number; // Frequency for ranking
}

export class PropertyAddressTrie {
  private root: TrieNode;
  private maxSuggestions: number;

  constructor(maxSuggestions = 10) {
    this.root = this.createNode();
    this.maxSuggestions = maxSuggestions;
  }

  private createNode(): TrieNode {
    return {
      children: new Map(),
      isEndOfWord: false,
      suggestions: [],
      count: 0
    };
  }

  /**
   * Insert an address into the trie
   * @param address The full address string
   * @param frequency Optional frequency/popularity weight
   */
  insert(address: string, frequency = 1): void {
    const normalized = address.toLowerCase().trim();
    let node = this.root;

    for (const char of normalized) {
      if (!node.children.has(char)) {
        node.children.set(char, this.createNode());
      }
      node = node.children.get(char)!;
      
      // Update suggestions at this node
      this.updateSuggestions(node, address, frequency);
    }

    node.isEndOfWord = true;
    node.count += frequency;
  }

  /**
   * Batch insert addresses with frequency data
   */
  batchInsert(addresses: Array<{ address: string; frequency?: number }>): void {
    addresses.forEach(({ address, frequency }) => {
      this.insert(address, frequency);
    });
  }

  /**
   * Update suggestions at a node, keeping only top N by frequency
   */
  private updateSuggestions(node: TrieNode, address: string, frequency: number): void {
    // Check if address already exists
    const existingIndex = node.suggestions.findIndex(s => s === address);
    if (existingIndex !== -1) {
      node.suggestions.splice(existingIndex, 1);
    }

    // Add address and sort by frequency (simplified - in production, store frequency with each)
    node.suggestions.push(address);
    
    // Keep only top suggestions
    if (node.suggestions.length > this.maxSuggestions) {
      node.suggestions = node.suggestions.slice(0, this.maxSuggestions);
    }
  }

  /**
   * Search for address suggestions based on prefix
   * @param prefix The search prefix
   * @param limit Maximum number of results
   * @returns Array of matching addresses
   */
  search(prefix: string, limit = 10): string[] {
    const normalized = prefix.toLowerCase().trim();
    let node = this.root;

    // Navigate to prefix endpoint
    for (const char of normalized) {
      if (!node.children.has(char)) {
        return []; // No matches
      }
      node = node.children.get(char)!;
    }

    // Return cached suggestions at this node
    return node.suggestions.slice(0, limit);
  }

  /**
   * Fuzzy search with tolerance for typos
   * Uses Levenshtein distance for similarity
   */
  fuzzySearch(prefix: string, limit = 10, tolerance = 2): string[] {
    const results: Array<{ address: string; distance: number }> = [];
    const normalized = prefix.toLowerCase().trim();

    const dfs = (node: TrieNode, currentWord: string, distance: number) => {
      if (distance > tolerance) return;

      if (node.isEndOfWord) {
        node.suggestions.forEach(suggestion => {
          const dist = this.levenshteinDistance(normalized, suggestion.toLowerCase());
          if (dist <= tolerance) {
            results.push({ address: suggestion, distance: dist });
          }
        });
      }

      // Continue searching children
      node.children.forEach((child, char) => {
        dfs(child, currentWord + char, distance);
      });
    };

    dfs(this.root, '', 0);

    // Sort by distance then alphabetically
    results.sort((a, b) => {
      if (a.distance !== b.distance) return a.distance - b.distance;
      return a.address.localeCompare(b.address);
    });

    return results.slice(0, limit).map(r => r.address);
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  private levenshteinDistance(str1: string, str2: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }

    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1, // substitution
            matrix[i][j - 1] + 1,     // insertion
            matrix[i - 1][j] + 1      // deletion
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  /**
   * Get statistics about the trie
   */
  getStats(): { totalNodes: number; totalWords: number; maxDepth: number } {
    let totalNodes = 0;
    let totalWords = 0;
    let maxDepth = 0;

    const traverse = (node: TrieNode, depth: number) => {
      totalNodes++;
      if (node.isEndOfWord) totalWords++;
      maxDepth = Math.max(maxDepth, depth);

      node.children.forEach(child => {
        traverse(child, depth + 1);
      });
    };

    traverse(this.root, 0);

    return { totalNodes, totalWords, maxDepth };
  }

  /**
   * Clear the trie
   */
  clear(): void {
    this.root = this.createNode();
  }
}

/**
 * City/Owner name trie with special handling for multi-word names
 */
export class NameTrie extends PropertyAddressTrie {
  /**
   * Insert name with special handling for surnames/business names
   */
  insert(name: string, frequency = 1): void {
    // Insert full name
    super.insert(name, frequency);

    // Also insert by last name for people (e.g., "John Smith" -> also searchable by "Smith")
    const parts = name.trim().split(/\s+/);
    if (parts.length > 1) {
      // Insert last word (likely surname)
      super.insert(parts[parts.length - 1], frequency / 2);
      
      // For business names with common suffixes
      const businessSuffixes = ['LLC', 'INC', 'CORP', 'LP', 'LLP', 'PA'];
      const lastPart = parts[parts.length - 1].toUpperCase();
      if (businessSuffixes.includes(lastPart) && parts.length > 2) {
        // Insert without business suffix for easier search
        const withoutSuffix = parts.slice(0, -1).join(' ');
        super.insert(withoutSuffix, frequency / 2);
      }
    }
  }
}

// Export singleton instances for the application
export const addressTrie = new PropertyAddressTrie(20);
export const cityTrie = new PropertyAddressTrie(10);
export const ownerTrie = new NameTrie(20);