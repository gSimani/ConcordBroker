/**
 * Graph data structure for entity relationship mapping
 * Tracks ownership networks, property portfolios, and business connections
 */

export interface EntityNode {
  id: string;
  type: 'person' | 'company' | 'property' | 'address';
  name: string;
  data: any;
  edges: Map<string, EntityEdge>;
}

export interface EntityEdge {
  to: string;
  type: 'owns' | 'manages' | 'related' | 'located_at' | 'partner' | 'subsidiary';
  weight: number; // Strength of relationship
  metadata?: any;
}

export class EntityGraph {
  private nodes: Map<string, EntityNode>;
  private adjacencyList: Map<string, Set<string>>;
  private reverseAdjacencyList: Map<string, Set<string>>; // For bidirectional queries

  constructor() {
    this.nodes = new Map();
    this.adjacencyList = new Map();
    this.reverseAdjacencyList = new Map();
  }

  /**
   * Add an entity node to the graph
   */
  addNode(id: string, type: EntityNode['type'], name: string, data?: any): void {
    if (!this.nodes.has(id)) {
      this.nodes.set(id, {
        id,
        type,
        name,
        data: data || {},
        edges: new Map()
      });
      this.adjacencyList.set(id, new Set());
      this.reverseAdjacencyList.set(id, new Set());
    }
  }

  /**
   * Add an edge between entities
   */
  addEdge(
    fromId: string,
    toId: string,
    type: EntityEdge['type'],
    weight = 1,
    metadata?: any
  ): void {
    // Ensure both nodes exist
    if (!this.nodes.has(fromId) || !this.nodes.has(toId)) {
      return;
    }

    const fromNode = this.nodes.get(fromId)!;
    fromNode.edges.set(toId, { to: toId, type, weight, metadata });

    // Update adjacency lists
    this.adjacencyList.get(fromId)!.add(toId);
    this.reverseAdjacencyList.get(toId)!.add(fromId);
  }

  /**
   * Find all properties owned by an entity
   */
  findOwnedProperties(entityId: string): Array<{ id: string; data: any }> {
    const node = this.nodes.get(entityId);
    if (!node) return [];

    const properties: Array<{ id: string; data: any }> = [];
    
    node.edges.forEach((edge, targetId) => {
      if (edge.type === 'owns') {
        const targetNode = this.nodes.get(targetId);
        if (targetNode && targetNode.type === 'property') {
          properties.push({
            id: targetNode.id,
            data: targetNode.data
          });
        }
      }
    });

    return properties;
  }

  /**
   * Find all entities that own a specific property
   */
  findPropertyOwners(propertyId: string): Array<{ id: string; name: string; type: string }> {
    const owners: Array<{ id: string; name: string; type: string }> = [];
    const reverseEdges = this.reverseAdjacencyList.get(propertyId);

    if (reverseEdges) {
      reverseEdges.forEach(entityId => {
        const entityNode = this.nodes.get(entityId);
        if (entityNode) {
          const edge = entityNode.edges.get(propertyId);
          if (edge && edge.type === 'owns') {
            owners.push({
              id: entityNode.id,
              name: entityNode.name,
              type: entityNode.type
            });
          }
        }
      });
    }

    return owners;
  }

  /**
   * Find connected entities using BFS
   * @param startId Starting entity ID
   * @param maxDepth Maximum depth to search
   * @param edgeTypes Optional filter for edge types
   */
  findConnectedEntities(
    startId: string,
    maxDepth = 2,
    edgeTypes?: EntityEdge['type'][]
  ): Map<string, { distance: number; path: string[] }> {
    const visited = new Map<string, { distance: number; path: string[] }>();
    const queue: Array<{ id: string; distance: number; path: string[] }> = [];

    if (!this.nodes.has(startId)) return visited;

    queue.push({ id: startId, distance: 0, path: [startId] });
    visited.set(startId, { distance: 0, path: [startId] });

    while (queue.length > 0) {
      const { id, distance, path } = queue.shift()!;

      if (distance >= maxDepth) continue;

      const node = this.nodes.get(id);
      if (!node) continue;

      node.edges.forEach((edge, targetId) => {
        // Filter by edge type if specified
        if (edgeTypes && !edgeTypes.includes(edge.type)) return;

        if (!visited.has(targetId)) {
          const newPath = [...path, targetId];
          visited.set(targetId, { distance: distance + 1, path: newPath });
          queue.push({ id: targetId, distance: distance + 1, path: newPath });
        }
      });
    }

    return visited;
  }

  /**
   * Find shortest path between two entities (Dijkstra's algorithm)
   */
  findShortestPath(startId: string, endId: string): string[] | null {
    if (!this.nodes.has(startId) || !this.nodes.has(endId)) return null;

    const distances = new Map<string, number>();
    const previous = new Map<string, string | null>();
    const unvisited = new Set<string>();

    // Initialize
    this.nodes.forEach((_, id) => {
      distances.set(id, id === startId ? 0 : Infinity);
      previous.set(id, null);
      unvisited.add(id);
    });

    while (unvisited.size > 0) {
      // Find unvisited node with minimum distance
      let current: string | null = null;
      let minDistance = Infinity;

      unvisited.forEach(id => {
        const distance = distances.get(id)!;
        if (distance < minDistance) {
          minDistance = distance;
          current = id;
        }
      });

      if (current === null || current === endId) break;

      unvisited.delete(current);

      // Update distances to neighbors
      const node = this.nodes.get(current)!;
      node.edges.forEach((edge, neighbor) => {
        if (unvisited.has(neighbor)) {
          const altDistance = distances.get(current)! + edge.weight;
          if (altDistance < distances.get(neighbor)!) {
            distances.set(neighbor, altDistance);
            previous.set(neighbor, current);
          }
        }
      });
    }

    // Reconstruct path
    const path: string[] = [];
    let current: string | null = endId;

    while (current !== null) {
      path.unshift(current);
      current = previous.get(current) ?? null;
    }

    return path.length > 1 && path[0] === startId ? path : null;
  }

  /**
   * Detect communities/clusters using Louvain algorithm (simplified)
   */
  detectCommunities(): Map<string, Set<string>> {
    const communities = new Map<string, Set<string>>();
    const visited = new Set<string>();
    let communityId = 0;

    // Simple connected components as communities
    this.nodes.forEach((_, nodeId) => {
      if (!visited.has(nodeId)) {
        const community = new Set<string>();
        const queue = [nodeId];

        while (queue.length > 0) {
          const current = queue.shift()!;
          if (visited.has(current)) continue;

          visited.add(current);
          community.add(current);

          // Add all neighbors
          const neighbors = this.adjacencyList.get(current);
          if (neighbors) {
            neighbors.forEach(neighbor => {
              if (!visited.has(neighbor)) {
                queue.push(neighbor);
              }
            });
          }
        }

        communities.set(`community_${communityId++}`, community);
      }
    });

    return communities;
  }

  /**
   * Calculate PageRank for entities (importance score)
   */
  calculatePageRank(iterations = 50, dampingFactor = 0.85): Map<string, number> {
    const pageRank = new Map<string, number>();
    const nodeCount = this.nodes.size;

    // Initialize with equal rank
    this.nodes.forEach((_, id) => {
      pageRank.set(id, 1 / nodeCount);
    });

    // Iterate
    for (let i = 0; i < iterations; i++) {
      const newPageRank = new Map<string, number>();

      this.nodes.forEach((_, id) => {
        let rank = (1 - dampingFactor) / nodeCount;

        // Sum contributions from incoming links
        const incomingLinks = this.reverseAdjacencyList.get(id);
        if (incomingLinks) {
          incomingLinks.forEach(linkId => {
            const linkNode = this.nodes.get(linkId);
            if (linkNode) {
              const outgoingCount = linkNode.edges.size || 1;
              rank += dampingFactor * (pageRank.get(linkId)! / outgoingCount);
            }
          });
        }

        newPageRank.set(id, rank);
      });

      // Update ranks
      newPageRank.forEach((rank, id) => {
        pageRank.set(id, rank);
      });
    }

    return pageRank;
  }

  /**
   * Find entities with most connections (degree centrality)
   */
  findMostConnected(limit = 10): Array<{ id: string; name: string; connections: number }> {
    const degrees: Array<{ id: string; name: string; connections: number }> = [];

    this.nodes.forEach((node, id) => {
      const outgoing = this.adjacencyList.get(id)?.size || 0;
      const incoming = this.reverseAdjacencyList.get(id)?.size || 0;
      
      degrees.push({
        id,
        name: node.name,
        connections: outgoing + incoming
      });
    });

    return degrees
      .sort((a, b) => b.connections - a.connections)
      .slice(0, limit);
  }

  /**
   * Find portfolio overlap between entities
   */
  findPortfolioOverlap(entity1Id: string, entity2Id: string): Array<{ id: string; data: any }> {
    const properties1 = new Set(this.findOwnedProperties(entity1Id).map(p => p.id));
    const properties2 = new Set(this.findOwnedProperties(entity2Id).map(p => p.id));

    const overlap: Array<{ id: string; data: any }> = [];

    properties1.forEach(propId => {
      if (properties2.has(propId)) {
        const node = this.nodes.get(propId);
        if (node) {
          overlap.push({ id: propId, data: node.data });
        }
      }
    });

    return overlap;
  }

  /**
   * Export graph to JSON format
   */
  toJSON(): {
    nodes: Array<any>;
    edges: Array<{ from: string; to: string; type: string; weight: number }>;
  } {
    const nodes: Array<any> = [];
    const edges: Array<{ from: string; to: string; type: string; weight: number }> = [];

    this.nodes.forEach(node => {
      nodes.push({
        id: node.id,
        type: node.type,
        name: node.name,
        data: node.data
      });

      node.edges.forEach((edge, toId) => {
        edges.push({
          from: node.id,
          to: toId,
          type: edge.type,
          weight: edge.weight
        });
      });
    });

    return { nodes, edges };
  }

  /**
   * Get graph statistics
   */
  getStats(): {
    nodeCount: number;
    edgeCount: number;
    avgDegree: number;
    nodeTypes: Map<string, number>;
    edgeTypes: Map<string, number>;
  } {
    const nodeTypes = new Map<string, number>();
    const edgeTypes = new Map<string, number>();
    let totalEdges = 0;

    this.nodes.forEach(node => {
      // Count node types
      const count = nodeTypes.get(node.type) || 0;
      nodeTypes.set(node.type, count + 1);

      // Count edge types
      node.edges.forEach(edge => {
        const edgeCount = edgeTypes.get(edge.type) || 0;
        edgeTypes.set(edge.type, edgeCount + 1);
        totalEdges++;
      });
    });

    return {
      nodeCount: this.nodes.size,
      edgeCount: totalEdges,
      avgDegree: this.nodes.size > 0 ? (totalEdges * 2) / this.nodes.size : 0,
      nodeTypes,
      edgeTypes
    };
  }

  /**
   * Clear the graph
   */
  clear(): void {
    this.nodes.clear();
    this.adjacencyList.clear();
    this.reverseAdjacencyList.clear();
  }
}

// Export singleton instance
export const entityGraph = new EntityGraph();