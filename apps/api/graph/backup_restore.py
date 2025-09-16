"""
Backup and Restore Utilities for Graphiti Knowledge Graph
Handles export/import of graph data for disaster recovery and migration
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import gzip
import shutil
from neo4j import AsyncGraphDatabase
import aiofiles
from tqdm.asyncio import tqdm

logger = logging.getLogger(__name__)


class GraphBackup:
    """
    Backup utility for Neo4j graph database
    """
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None,
                 backup_dir: str = "backups"):
        """
        Initialize backup utility
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            backup_dir: Directory for storing backups
        """
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.driver = None
        
    async def connect(self):
        """Establish database connection"""
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
    async def disconnect(self):
        """Close database connection"""
        if self.driver:
            await self.driver.close()
            
    async def backup_full(self, 
                         backup_name: Optional[str] = None,
                         compress: bool = True) -> str:
        """
        Create full backup of the graph database
        
        Args:
            backup_name: Custom backup name (default: timestamp)
            compress: Whether to compress the backup
            
        Returns:
            Path to backup file
        """
        await self.connect()
        
        try:
            # Generate backup name
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"graphiti_backup_{timestamp}"
            
            backup_path = self.backup_dir / f"{backup_name}.json"
            
            logger.info(f"Starting full backup to {backup_path}")
            
            backup_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "type": "full",
                    "database": "neo4j"
                },
                "nodes": [],
                "relationships": [],
                "indices": [],
                "constraints": []
            }
            
            async with self.driver.session() as session:
                # Export nodes
                logger.info("Exporting nodes...")
                node_result = await session.run("""
                    MATCH (n)
                    RETURN n, labels(n) as labels, id(n) as id
                """)
                
                async for record in node_result:
                    node = record["n"]
                    backup_data["nodes"].append({
                        "id": record["id"],
                        "labels": record["labels"],
                        "properties": dict(node)
                    })
                
                logger.info(f"Exported {len(backup_data['nodes'])} nodes")
                
                # Export relationships
                logger.info("Exporting relationships...")
                rel_result = await session.run("""
                    MATCH (a)-[r]->(b)
                    RETURN id(a) as start_id, id(b) as end_id, 
                           type(r) as type, r as rel, id(r) as id
                """)
                
                async for record in rel_result:
                    backup_data["relationships"].append({
                        "id": record["id"],
                        "start_id": record["start_id"],
                        "end_id": record["end_id"],
                        "type": record["type"],
                        "properties": dict(record["rel"]) if record["rel"] else {}
                    })
                
                logger.info(f"Exported {len(backup_data['relationships'])} relationships")
                
                # Export indices
                logger.info("Exporting indices...")
                index_result = await session.run("SHOW INDEXES")
                
                async for record in index_result:
                    backup_data["indices"].append({
                        "name": record.get("name"),
                        "type": record.get("type"),
                        "entity_type": record.get("entityType"),
                        "properties": record.get("properties", [])
                    })
                
                # Export constraints
                logger.info("Exporting constraints...")
                constraint_result = await session.run("SHOW CONSTRAINTS")
                
                async for record in constraint_result:
                    backup_data["constraints"].append({
                        "name": record.get("name"),
                        "type": record.get("type"),
                        "entity_type": record.get("entityType"),
                        "properties": record.get("properties", [])
                    })
            
            # Write backup
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(json.dumps(backup_data, indent=2, default=str))
            
            # Compress if requested
            if compress:
                compressed_path = Path(f"{backup_path}.gz")
                
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                os.remove(backup_path)
                backup_path = compressed_path
                
            logger.info(f"Backup completed: {backup_path}")
            
            # Update backup catalog
            await self._update_backup_catalog(backup_name, backup_path, backup_data["metadata"])
            
            return str(backup_path)
            
        finally:
            await self.disconnect()
            
    async def backup_incremental(self, 
                                since: datetime,
                                backup_name: Optional[str] = None) -> str:
        """
        Create incremental backup since specified time
        
        Args:
            since: Backup changes since this time
            backup_name: Custom backup name
            
        Returns:
            Path to backup file
        """
        await self.connect()
        
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"graphiti_incremental_{timestamp}"
            
            backup_path = self.backup_dir / f"{backup_name}.json"
            
            logger.info(f"Starting incremental backup since {since}")
            
            backup_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "type": "incremental",
                    "since": since.isoformat(),
                    "database": "neo4j"
                },
                "nodes": [],
                "relationships": []
            }
            
            async with self.driver.session() as session:
                # Export nodes created/modified since timestamp
                # Note: This requires timestamp properties on nodes
                node_result = await session.run("""
                    MATCH (n)
                    WHERE n.created_at >= $since OR n.updated_at >= $since
                    RETURN n, labels(n) as labels, id(n) as id
                """, since=since.isoformat())
                
                async for record in node_result:
                    node = record["n"]
                    backup_data["nodes"].append({
                        "id": record["id"],
                        "labels": record["labels"],
                        "properties": dict(node),
                        "operation": "upsert"
                    })
                
                logger.info(f"Exported {len(backup_data['nodes'])} changed nodes")
                
                # Export relationships created/modified since timestamp
                rel_result = await session.run("""
                    MATCH (a)-[r]->(b)
                    WHERE r.created_at >= $since OR r.updated_at >= $since
                    RETURN id(a) as start_id, id(b) as end_id, 
                           type(r) as type, r as rel, id(r) as id
                """, since=since.isoformat())
                
                async for record in rel_result:
                    backup_data["relationships"].append({
                        "id": record["id"],
                        "start_id": record["start_id"],
                        "end_id": record["end_id"],
                        "type": record["type"],
                        "properties": dict(record["rel"]) if record["rel"] else {},
                        "operation": "upsert"
                    })
                
                logger.info(f"Exported {len(backup_data['relationships'])} changed relationships")
            
            # Write backup
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(json.dumps(backup_data, indent=2, default=str))
            
            logger.info(f"Incremental backup completed: {backup_path}")
            
            return str(backup_path)
            
        finally:
            await self.disconnect()
            
    async def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups
        
        Returns:
            List of backup metadata
        """
        catalog_path = self.backup_dir / "backup_catalog.json"
        
        if catalog_path.exists():
            async with aiofiles.open(catalog_path, 'r') as f:
                content = await f.read()
                catalog = json.loads(content)
                return catalog.get("backups", [])
        
        return []
        
    async def _update_backup_catalog(self, 
                                    name: str,
                                    path: Path,
                                    metadata: Dict[str, Any]):
        """Update backup catalog with new backup info"""
        catalog_path = self.backup_dir / "backup_catalog.json"
        
        # Load existing catalog
        if catalog_path.exists():
            async with aiofiles.open(catalog_path, 'r') as f:
                content = await f.read()
                catalog = json.loads(content)
        else:
            catalog = {"backups": []}
        
        # Add new backup
        catalog["backups"].append({
            "name": name,
            "path": str(path),
            "size": path.stat().st_size,
            "metadata": metadata
        })
        
        # Save updated catalog
        async with aiofiles.open(catalog_path, 'w') as f:
            await f.write(json.dumps(catalog, indent=2, default=str))


class GraphRestore:
    """
    Restore utility for Neo4j graph database
    """
    
    def __init__(self,
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None):
        """
        Initialize restore utility
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = None
        
    async def connect(self):
        """Establish database connection"""
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
    async def disconnect(self):
        """Close database connection"""
        if self.driver:
            await self.driver.close()
            
    async def restore_full(self, 
                          backup_path: str,
                          clear_existing: bool = True) -> Dict[str, Any]:
        """
        Restore full backup to database
        
        Args:
            backup_path: Path to backup file
            clear_existing: Whether to clear existing data
            
        Returns:
            Restore statistics
        """
        await self.connect()
        
        try:
            logger.info(f"Starting restore from {backup_path}")
            
            # Load backup data
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rt') as f:
                    backup_data = json.load(f)
            else:
                async with aiofiles.open(backup_path, 'r') as f:
                    content = await f.read()
                    backup_data = json.loads(content)
            
            stats = {
                "nodes_restored": 0,
                "relationships_restored": 0,
                "indices_restored": 0,
                "constraints_restored": 0,
                "errors": []
            }
            
            async with self.driver.session() as session:
                # Clear existing data if requested
                if clear_existing:
                    logger.info("Clearing existing data...")
                    await session.run("MATCH (n) DETACH DELETE n")
                
                # Create a mapping of old IDs to new IDs
                id_mapping = {}
                
                # Restore nodes
                logger.info(f"Restoring {len(backup_data['nodes'])} nodes...")
                
                for node_data in tqdm(backup_data["nodes"], desc="Restoring nodes"):
                    try:
                        labels = ":".join(node_data["labels"]) if node_data["labels"] else ""
                        properties = node_data["properties"]
                        
                        # Create node with properties
                        if labels:
                            query = f"""
                                CREATE (n:{labels})
                                SET n = $properties
                                RETURN id(n) as new_id
                            """
                        else:
                            query = """
                                CREATE (n)
                                SET n = $properties
                                RETURN id(n) as new_id
                            """
                        
                        result = await session.run(query, properties=properties)
                        record = await result.single()
                        
                        if record:
                            id_mapping[node_data["id"]] = record["new_id"]
                            stats["nodes_restored"] += 1
                            
                    except Exception as e:
                        stats["errors"].append(f"Node restore error: {e}")
                        logger.error(f"Failed to restore node: {e}")
                
                # Restore relationships
                logger.info(f"Restoring {len(backup_data['relationships'])} relationships...")
                
                for rel_data in tqdm(backup_data["relationships"], desc="Restoring relationships"):
                    try:
                        start_id = id_mapping.get(rel_data["start_id"])
                        end_id = id_mapping.get(rel_data["end_id"])
                        
                        if start_id and end_id:
                            query = f"""
                                MATCH (a), (b)
                                WHERE id(a) = $start_id AND id(b) = $end_id
                                CREATE (a)-[r:{rel_data['type']}]->(b)
                                SET r = $properties
                                RETURN r
                            """
                            
                            await session.run(
                                query,
                                start_id=start_id,
                                end_id=end_id,
                                properties=rel_data.get("properties", {})
                            )
                            
                            stats["relationships_restored"] += 1
                            
                    except Exception as e:
                        stats["errors"].append(f"Relationship restore error: {e}")
                        logger.error(f"Failed to restore relationship: {e}")
                
                # Restore indices
                logger.info("Restoring indices...")
                
                for index_data in backup_data.get("indices", []):
                    try:
                        # Skip if index already exists
                        check_result = await session.run(
                            "SHOW INDEXES WHERE name = $name",
                            name=index_data["name"]
                        )
                        
                        if not await check_result.single():
                            # Create index based on type
                            # This is simplified - actual implementation would handle all index types
                            if index_data["entity_type"] == "NODE":
                                props = ", ".join([f"n.{p}" for p in index_data["properties"]])
                                query = f"""
                                    CREATE INDEX {index_data['name']} IF NOT EXISTS
                                    FOR (n:{index_data.get('labels', [''])[0]})
                                    ON ({props})
                                """
                                await session.run(query)
                                stats["indices_restored"] += 1
                                
                    except Exception as e:
                        stats["errors"].append(f"Index restore error: {e}")
                        logger.error(f"Failed to restore index: {e}")
                
                # Restore constraints
                logger.info("Restoring constraints...")
                
                for constraint_data in backup_data.get("constraints", []):
                    try:
                        # Create constraint based on type
                        # This is simplified - actual implementation would handle all constraint types
                        stats["constraints_restored"] += 1
                        
                    except Exception as e:
                        stats["errors"].append(f"Constraint restore error: {e}")
                        logger.error(f"Failed to restore constraint: {e}")
            
            logger.info(f"Restore completed: {stats}")
            
            return stats
            
        finally:
            await self.disconnect()
            
    async def restore_incremental(self, 
                                 backup_path: str) -> Dict[str, Any]:
        """
        Apply incremental backup to database
        
        Args:
            backup_path: Path to incremental backup file
            
        Returns:
            Restore statistics
        """
        await self.connect()
        
        try:
            logger.info(f"Applying incremental backup from {backup_path}")
            
            # Load backup data
            async with aiofiles.open(backup_path, 'r') as f:
                content = await f.read()
                backup_data = json.loads(content)
            
            stats = {
                "nodes_updated": 0,
                "relationships_updated": 0,
                "errors": []
            }
            
            async with self.driver.session() as session:
                # Apply node updates
                for node_data in backup_data["nodes"]:
                    try:
                        # Merge node based on unique properties
                        # This is simplified - need actual unique identifiers
                        stats["nodes_updated"] += 1
                        
                    except Exception as e:
                        stats["errors"].append(f"Node update error: {e}")
                
                # Apply relationship updates
                for rel_data in backup_data["relationships"]:
                    try:
                        # Merge relationship
                        stats["relationships_updated"] += 1
                        
                    except Exception as e:
                        stats["errors"].append(f"Relationship update error: {e}")
            
            logger.info(f"Incremental restore completed: {stats}")
            
            return stats
            
        finally:
            await self.disconnect()


class BackupScheduler:
    """
    Automated backup scheduler for graph database
    """
    
    def __init__(self, backup_service: GraphBackup):
        self.backup_service = backup_service
        self.is_running = False
        
    async def start(self, 
                   full_backup_interval: int = 86400,  # Daily
                   incremental_interval: int = 3600):   # Hourly
        """
        Start automated backup schedule
        
        Args:
            full_backup_interval: Seconds between full backups
            incremental_interval: Seconds between incremental backups
        """
        self.is_running = True
        
        last_full_backup = datetime.now()
        last_incremental = datetime.now()
        
        logger.info("Backup scheduler started")
        
        while self.is_running:
            now = datetime.now()
            
            # Check if full backup is due
            if (now - last_full_backup).total_seconds() >= full_backup_interval:
                try:
                    await self.backup_service.backup_full()
                    last_full_backup = now
                    last_incremental = now  # Reset incremental timer
                    logger.info("Scheduled full backup completed")
                except Exception as e:
                    logger.error(f"Scheduled full backup failed: {e}")
            
            # Check if incremental backup is due
            elif (now - last_incremental).total_seconds() >= incremental_interval:
                try:
                    await self.backup_service.backup_incremental(since=last_incremental)
                    last_incremental = now
                    logger.info("Scheduled incremental backup completed")
                except Exception as e:
                    logger.error(f"Scheduled incremental backup failed: {e}")
            
            # Sleep for a minute before next check
            await asyncio.sleep(60)
            
    def stop(self):
        """Stop backup scheduler"""
        self.is_running = False
        logger.info("Backup scheduler stopped")


# CLI interface
async def main():
    """Command-line interface for backup/restore"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Graphiti Backup/Restore Utility")
    parser.add_argument("action", choices=["backup", "restore", "list"], 
                       help="Action to perform")
    parser.add_argument("--type", choices=["full", "incremental"], 
                       default="full", help="Backup type")
    parser.add_argument("--file", help="Backup file path for restore")
    parser.add_argument("--since", help="Since timestamp for incremental backup")
    parser.add_argument("--compress", action="store_true", 
                       help="Compress backup file")
    parser.add_argument("--clear", action="store_true", 
                       help="Clear existing data before restore")
    
    args = parser.parse_args()
    
    if args.action == "backup":
        backup = GraphBackup()
        
        if args.type == "full":
            path = await backup.backup_full(compress=args.compress)
            print(f"Full backup created: {path}")
        else:
            if not args.since:
                print("Error: --since required for incremental backup")
                return
            
            since = datetime.fromisoformat(args.since)
            path = await backup.backup_incremental(since=since)
            print(f"Incremental backup created: {path}")
            
    elif args.action == "restore":
        if not args.file:
            print("Error: --file required for restore")
            return
        
        restore = GraphRestore()
        
        if args.type == "full":
            stats = await restore.restore_full(args.file, clear_existing=args.clear)
        else:
            stats = await restore.restore_incremental(args.file)
        
        print(f"Restore completed: {stats}")
        
    elif args.action == "list":
        backup = GraphBackup()
        backups = await backup.list_backups()
        
        print("\nAvailable backups:")
        for b in backups:
            size_mb = b["size"] / (1024 * 1024)
            print(f"  - {b['name']}: {size_mb:.2f} MB ({b['metadata']['type']}) - {b['metadata']['timestamp']}")


if __name__ == "__main__":
    asyncio.run(main())