"""
Graphiti Initialization Script for ConcordBroker
Sets up Neo4j database, creates indices, and verifies connectivity
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if Graphiti is available
try:
    from graphiti_core import Graphiti
    from graphiti_core.llm_client import OpenAIClient, LLMConfig
    from graphiti_core.embedder import OpenAIEmbedder
    from neo4j import AsyncGraphDatabase
    GRAPHITI_AVAILABLE = True
except ImportError as e:
    logger.error(f"Graphiti not installed: {e}")
    logger.info("Install with: pip install graphiti-core neo4j")
    GRAPHITI_AVAILABLE = False
    sys.exit(1)


class GraphitiInitializer:
    """Initialize and configure Graphiti for ConcordBroker"""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.graphiti = None
        self.driver = None
        
    async def check_neo4j_connection(self) -> bool:
        """Test Neo4j database connectivity"""
        try:
            logger.info(f"Testing Neo4j connection at {self.neo4j_uri}...")
            
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                
                if record and record["test"] == 1:
                    logger.info("✅ Neo4j connection successful!")
                    
                    # Get database info
                    info_result = await session.run("""
                        CALL dbms.components() 
                        YIELD name, versions, edition 
                        RETURN name, versions[0] as version, edition
                    """)
                    info = await info_result.single()
                    
                    if info:
                        logger.info(f"Neo4j Version: {info['version']}, Edition: {info['edition']}")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            logger.info("Make sure Neo4j is running:")
            logger.info("  Docker: docker run -p 7474:7474 -p 7687:7687 neo4j")
            logger.info("  Desktop: Start your Neo4j database")
            return False
        finally:
            if self.driver:
                await self.driver.close()
                
    async def initialize_graphiti(self) -> bool:
        """Initialize Graphiti with ConcordBroker configuration"""
        try:
            logger.info("Initializing Graphiti...")
            
            # Create Graphiti instance
            self.graphiti = Graphiti(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password,
                llm_client=OpenAIClient(
                    config=LLMConfig(
                        model=os.getenv("GRAPHITI_LLM_MODEL", "gpt-4o-mini"),
                        temperature=0.7,
                        max_tokens=4000
                    )
                ),
                embedder=OpenAIEmbedder(
                    model=os.getenv("GRAPHITI_EMBEDDING_MODEL", "text-embedding-3-small")
                )
            )
            
            # Build indices for better performance
            logger.info("Building Graphiti indices...")
            await self.graphiti.build_indices()
            
            logger.info("✅ Graphiti initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Graphiti initialization failed: {e}")
            return False
            
    async def create_property_indices(self) -> bool:
        """Create custom indices for property data"""
        try:
            logger.info("Creating property-specific indices...")
            
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            async with self.driver.session() as session:
                # Create indices for better query performance
                indices = [
                    # Property indices
                    "CREATE INDEX property_parcel_idx IF NOT EXISTS FOR (p:Property) ON (p.parcel_id)",
                    "CREATE INDEX property_county_idx IF NOT EXISTS FOR (p:Property) ON (p.county)",
                    "CREATE INDEX property_city_idx IF NOT EXISTS FOR (p:Property) ON (p.city)",
                    "CREATE INDEX property_value_idx IF NOT EXISTS FOR (p:Property) ON (p.current_value)",
                    
                    # Owner indices
                    "CREATE INDEX owner_name_idx IF NOT EXISTS FOR (o:Owner) ON (o.name)",
                    "CREATE INDEX owner_type_idx IF NOT EXISTS FOR (o:Owner) ON (o.entity_type)",
                    "CREATE INDEX owner_sunbiz_idx IF NOT EXISTS FOR (o:Owner) ON (o.sunbiz_id)",
                    
                    # Transaction indices
                    "CREATE INDEX transaction_date_idx IF NOT EXISTS FOR (t:Transaction) ON (t.date)",
                    "CREATE INDEX transaction_type_idx IF NOT EXISTS FOR (t:Transaction) ON (t.type)",
                    "CREATE INDEX transaction_amount_idx IF NOT EXISTS FOR (t:Transaction) ON (t.amount)",
                    
                    # Entity indices (Graphiti default)
                    "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                    "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
                    
                    # Episode indices (Graphiti default)
                    "CREATE INDEX episode_name_idx IF NOT EXISTS FOR (ep:Episode) ON (ep.name)",
                    "CREATE INDEX episode_time_idx IF NOT EXISTS FOR (ep:Episode) ON (ep.reference_time)"
                ]
                
                for index_query in indices:
                    try:
                        await session.run(index_query)
                        index_name = index_query.split("INDEX")[1].split("IF")[0].strip()
                        logger.info(f"  ✓ Created index: {index_name}")
                    except Exception as e:
                        logger.warning(f"  ⚠ Index creation warning: {e}")
                
                # Create full-text search indices
                fulltext_indices = [
                    ("property_search", "Property", ["address", "city", "county"]),
                    ("owner_search", "Owner", ["name", "email"]),
                    ("entity_search", "Entity", ["name", "description"])
                ]
                
                for idx_name, label, properties in fulltext_indices:
                    try:
                        props = ", ".join([f"n.{p}" for p in properties])
                        query = f"""
                        CALL db.index.fulltext.createNodeIndex(
                            '{idx_name}', 
                            ['{label}'], 
                            [{', '.join([f"'{p}'" for p in properties])}]
                        )
                        """
                        await session.run(query)
                        logger.info(f"  ✓ Created full-text index: {idx_name}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"  ✓ Full-text index exists: {idx_name}")
                        else:
                            logger.warning(f"  ⚠ Full-text index warning: {e}")
                
                logger.info("✅ Property indices created successfully!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
            return False
        finally:
            if self.driver:
                await self.driver.close()
                
    async def create_constraints(self) -> bool:
        """Create constraints for data integrity"""
        try:
            logger.info("Creating database constraints...")
            
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            async with self.driver.session() as session:
                constraints = [
                    # Uniqueness constraints
                    "CREATE CONSTRAINT property_parcel_unique IF NOT EXISTS FOR (p:Property) REQUIRE p.parcel_id IS UNIQUE",
                    "CREATE CONSTRAINT owner_sunbiz_unique IF NOT EXISTS FOR (o:Owner) REQUIRE o.sunbiz_id IS UNIQUE",
                    
                    # Existence constraints (Neo4j 5.0+)
                    "CREATE CONSTRAINT property_parcel_exists IF NOT EXISTS FOR (p:Property) REQUIRE p.parcel_id IS NOT NULL",
                    "CREATE CONSTRAINT owner_name_exists IF NOT EXISTS FOR (o:Owner) REQUIRE o.name IS NOT NULL"
                ]
                
                for constraint_query in constraints:
                    try:
                        await session.run(constraint_query)
                        constraint_name = constraint_query.split("CONSTRAINT")[1].split("IF")[0].strip()
                        logger.info(f"  ✓ Created constraint: {constraint_name}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            constraint_name = constraint_query.split("CONSTRAINT")[1].split("IF")[0].strip()
                            logger.info(f"  ✓ Constraint exists: {constraint_name}")
                        else:
                            logger.warning(f"  ⚠ Constraint warning: {e}")
                
                logger.info("✅ Constraints created successfully!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Constraint creation failed: {e}")
            return False
        finally:
            if self.driver:
                await self.driver.close()
                
    async def load_sample_data(self) -> bool:
        """Load sample property data for testing"""
        try:
            logger.info("Loading sample data...")
            
            # Import property graph service
            from property_graph_service import PropertyGraphService, PropertyNode, OwnerNode, TransactionEdge
            
            service = PropertyGraphService(
                neo4j_uri=self.neo4j_uri,
                neo4j_user=self.neo4j_user,
                neo4j_password=self.neo4j_password
            )
            
            # Sample properties
            properties = [
                PropertyNode(
                    parcel_id="SAMPLE_001",
                    address="123 Test Street",
                    city="Hollywood",
                    county="Broward",
                    property_type="Residential",
                    current_value=450000,
                    year_built=2005,
                    square_feet=2500,
                    bedrooms=3,
                    bathrooms=2.5
                ),
                PropertyNode(
                    parcel_id="SAMPLE_002",
                    address="456 Demo Avenue",
                    city="Fort Lauderdale",
                    county="Broward",
                    property_type="Commercial",
                    current_value=1200000,
                    year_built=2010,
                    square_feet=5000
                )
            ]
            
            # Sample owners
            owners = [
                OwnerNode(
                    name="John Sample",
                    entity_type="person",
                    phone="555-0001",
                    email="john.sample@example.com"
                ),
                OwnerNode(
                    name="Demo Properties LLC",
                    entity_type="corporation",
                    sunbiz_id="L24000123456"
                )
            ]
            
            # Add to graph
            for prop in properties:
                await service.add_property(prop)
                logger.info(f"  ✓ Added property: {prop.parcel_id}")
            
            for owner in owners:
                await service.add_owner(owner)
                logger.info(f"  ✓ Added owner: {owner.name}")
            
            # Create ownership relationships
            await service.add_ownership(
                parcel_id="SAMPLE_001",
                owner_name="John Sample",
                ownership_type="current",
                start_date=datetime(2020, 1, 1)
            )
            
            await service.add_ownership(
                parcel_id="SAMPLE_002",
                owner_name="Demo Properties LLC",
                ownership_type="current",
                start_date=datetime(2021, 6, 1)
            )
            
            logger.info("  ✓ Created ownership relationships")
            
            # Create a transaction
            await service.add_transaction(
                from_owner="Previous Owner",
                to_owner="John Sample",
                parcel_id="SAMPLE_001",
                transaction=TransactionEdge(
                    transaction_type="sale",
                    date=datetime(2020, 1, 1),
                    amount=425000,
                    document_number="DOC2020-001"
                )
            )
            
            logger.info("  ✓ Created transaction")
            
            logger.info("✅ Sample data loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sample data loading failed: {e}")
            return False
            
    async def verify_setup(self) -> Dict[str, Any]:
        """Verify the complete Graphiti setup"""
        try:
            logger.info("\nVerifying Graphiti setup...")
            
            verification = {
                "neo4j_connected": False,
                "graphiti_initialized": False,
                "indices_created": False,
                "constraints_created": False,
                "sample_data_loaded": False,
                "node_count": 0,
                "edge_count": 0,
                "status": "unknown"
            }
            
            # Check Neo4j
            verification["neo4j_connected"] = await self.check_neo4j_connection()
            
            if not verification["neo4j_connected"]:
                verification["status"] = "neo4j_error"
                return verification
            
            # Initialize Graphiti
            verification["graphiti_initialized"] = await self.initialize_graphiti()
            
            if not verification["graphiti_initialized"]:
                verification["status"] = "graphiti_error"
                return verification
            
            # Create indices
            verification["indices_created"] = await self.create_property_indices()
            
            # Create constraints
            verification["constraints_created"] = await self.create_constraints()
            
            # Get graph statistics
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            async with self.driver.session() as session:
                # Count nodes
                node_result = await session.run("MATCH (n) RETURN count(n) as count")
                node_record = await node_result.single()
                verification["node_count"] = node_record["count"] if node_record else 0
                
                # Count edges
                edge_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
                edge_record = await edge_result.single()
                verification["edge_count"] = edge_record["count"] if edge_record else 0
            
            await self.driver.close()
            
            # Load sample data if graph is empty
            if verification["node_count"] == 0:
                logger.info("Graph is empty, loading sample data...")
                verification["sample_data_loaded"] = await self.load_sample_data()
            else:
                logger.info(f"Graph already contains {verification['node_count']} nodes")
                verification["sample_data_loaded"] = True
            
            # Determine overall status
            if all([
                verification["neo4j_connected"],
                verification["graphiti_initialized"],
                verification["indices_created"]
            ]):
                verification["status"] = "ready"
            else:
                verification["status"] = "partial"
            
            return verification
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def display_summary(self, verification: Dict[str, Any]):
        """Display setup summary"""
        print("\n" + "="*60)
        print("GRAPHITI SETUP SUMMARY")
        print("="*60)
        
        status_symbols = {
            True: "✅",
            False: "❌"
        }
        
        print(f"\nComponents:")
        print(f"  {status_symbols[verification.get('neo4j_connected', False)]} Neo4j Connection")
        print(f"  {status_symbols[verification.get('graphiti_initialized', False)]} Graphiti Initialization")
        print(f"  {status_symbols[verification.get('indices_created', False)]} Database Indices")
        print(f"  {status_symbols[verification.get('constraints_created', False)]} Database Constraints")
        print(f"  {status_symbols[verification.get('sample_data_loaded', False)]} Sample Data")
        
        print(f"\nGraph Statistics:")
        print(f"  Nodes: {verification.get('node_count', 0)}")
        print(f"  Edges: {verification.get('edge_count', 0)}")
        
        print(f"\nOverall Status: {verification.get('status', 'unknown').upper()}")
        
        if verification.get('status') == 'ready':
            print("\n🎉 Graphiti is ready to use!")
            print("\nNext steps:")
            print("  1. Run data migration: python apps/api/graph/migrate_data.py")
            print("  2. Start API with graph: python apps/api/main_simple.py")
            print("  3. Access Neo4j Browser: http://localhost:7474")
        elif verification.get('status') == 'partial':
            print("\n⚠️ Graphiti is partially configured.")
            print("Check the logs above for any errors.")
        else:
            print("\n❌ Graphiti setup failed.")
            print("Please resolve the errors and try again.")
        
        print("\n" + "="*60)


async def main():
    """Main initialization function"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           GRAPHITI INITIALIZATION FOR CONCORDBROKER       ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    initializer = GraphitiInitializer()
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY not found in environment")
        logger.info("Add to .env file: OPENAI_API_KEY=your_key_here")
        sys.exit(1)
    
    # Run verification
    verification = await initializer.verify_setup()
    
    # Display summary
    await initializer.display_summary(verification)
    
    # Return status code
    if verification.get('status') == 'ready':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())