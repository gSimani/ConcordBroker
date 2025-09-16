/**
 * ConcordBroker Algorithm Suite
 * High-performance data structures and algorithms for real estate intelligence
 */

// Trie for autocomplete
export { 
  PropertyAddressTrie, 
  NameTrie,
  addressTrie,
  cityTrie,
  ownerTrie 
} from './property-trie';

// Heap for scoring
export { 
  PropertyHeap, 
  TopKPropertyHeap,
  type ScoredProperty 
} from './property-heap';

// BST for range queries
export { 
  PropertyBST, 
  MultiPropertyBST,
  type PropertyNode 
} from './property-bst';

// Cache for performance
export { 
  PropertyLRUCache,
  PropertyTTLCache,
  PropertyHybridCache,
  propertyCache,
  searchCache,
  apiResponseCache 
} from './property-cache';

// Graph for relationships
export { 
  EntityGraph,
  entityGraph,
  type EntityNode,
  type EntityEdge 
} from './entity-graph';

// Algorithm utilities
export { AlgorithmService } from './algorithm-service';