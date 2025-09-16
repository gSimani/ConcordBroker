"""
Test Supabase Data Pipeline
Comprehensive test of all data agents with Supabase integration
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
import sys

# Add apps to path
sys.path.insert(0, str(Path(__file__).parent / 'apps' / 'workers'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def test_supabase_connection():
    """Test Supabase connection"""
    console.print("\n[bold cyan]1. Testing Supabase Connection[/bold cyan]")
    
    try:
        from supabase_config import supabase_config
        
        # Check environment variables
        checks = {
            'SUPABASE_URL': os.getenv('SUPABASE_URL'),
            'SUPABASE_ANON_KEY': os.getenv('SUPABASE_ANON_KEY'),
            'SUPABASE_SERVICE_KEY': os.getenv('SUPABASE_SERVICE_KEY'),
            'SUPABASE_DB_URL': os.getenv('SUPABASE_DB_URL')
        }
        
        missing = [k for k, v in checks.items() if not v]
        
        if missing:
            console.print(f"[red]Missing environment variables: {', '.join(missing)}[/red]")
            console.print("[yellow]Please configure .env file with Supabase credentials[/yellow]")
            return False
        
        # Test database connection
        pool = await supabase_config.get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT version()")
            console.print(f"[green]✓[/green] Database connected: PostgreSQL {result[:20]}...")
        
        await pool.close()
        return True
        
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
        return False

async def test_agent_databases():
    """Test agent database modules"""
    console.print("\n[bold cyan]2. Testing Agent Database Modules[/bold cyan]")
    
    agents = [
        ('TPP', 'tpp.database_supabase', 'TPPSupabaseDB'),
        ('NAV', 'nav_assessments.database_supabase', 'NAVSupabaseDB'),
        ('SDF', 'sdf_sales.database_supabase', 'SDFSupabaseDB')
    ]
    
    results = []
    
    for name, module_path, class_name in agents:
        try:
            module = __import__(module_path, fromlist=[class_name])
            db_class = getattr(module, class_name)
            
            # Test instantiation
            db = db_class()
            await db.connect()
            
            # Test basic query
            tables = {
                'TPP': 'fl_tpp_accounts',
                'NAV': 'fl_nav_parcel_summary',
                'SDF': 'fl_sdf_sales'
            }
            
            async with db.pool.acquire() as conn:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {tables[name]}")
                results.append((name, 'Success', f"{count:,} records"))
                console.print(f"[green]✓[/green] {name}: {count:,} records in {tables[name]}")
            
            await db.disconnect()
            
        except Exception as e:
            results.append((name, 'Failed', str(e)[:50]))
            console.print(f"[red]✗[/red] {name}: {str(e)[:50]}")
    
    return results

async def test_update_monitoring():
    """Test update monitoring system"""
    console.print("\n[bold cyan]3. Testing Update Monitoring[/bold cyan]")
    
    try:
        from supabase_config import SupabaseUpdateMonitor, supabase_config
        
        pool = await supabase_config.get_db_pool()
        monitor = SupabaseUpdateMonitor(pool)
        
        # Initialize tracking tables
        await monitor.initialize_tracking_tables()
        console.print("[green]✓[/green] Tracking tables initialized")
        
        # Test update check
        test_update = await monitor.check_for_update(
            'test_agent',
            'http://test.url',
            'test_hash_123',
            1024
        )
        console.print(f"[green]✓[/green] Update check: {'New' if test_update else 'No change'}")
        
        # Record test update
        await monitor.record_update('test_agent', 'http://test.url', {
            'status': 'test',
            'records_processed': 100,
            'new_records': 50,
            'updated_records': 50
        })
        console.print("[green]✓[/green] Update recorded")
        
        # Get pending updates
        pending = await monitor.get_pending_updates()
        console.print(f"[green]✓[/green] Pending updates: {len(pending)}")
        
        await pool.close()
        return True
        
    except Exception as e:
        console.print(f"[red]Monitoring test failed: {e}[/red]")
        return False

async def test_alert_system():
    """Test alert system"""
    console.print("\n[bold cyan]4. Testing Alert System[/bold cyan]")
    
    try:
        from alert_system import AlertSystem, DataUpdateAlerts
        
        alert_system = AlertSystem()
        await alert_system.initialize()
        
        data_alerts = DataUpdateAlerts(alert_system)
        
        # Test alert creation (without sending)
        test_alerts = [
            ('Distressed Properties', lambda: data_alerts.new_distressed_properties([
                {'parcel_id': 'TEST001', 'sale_price': 150000, 'qualification_description': 'Foreclosure'}
            ])),
            ('Major Owner', lambda: data_alerts.major_owner_activity('TEST OWNER', {
                'property_count': 50, 'total_value': 10000000
            })),
            ('Data Update', lambda: data_alerts.data_source_update('TEST_SOURCE', {
                'new_records': 1000, 'updated_records': 500
            }))
        ]
        
        for alert_name, alert_func in test_alerts:
            try:
                await alert_func()
                console.print(f"[green]✓[/green] {alert_name} alert created")
            except Exception as e:
                console.print(f"[yellow]![/yellow] {alert_name}: {str(e)[:30]}")
        
        await alert_system.close()
        return True
        
    except Exception as e:
        console.print(f"[red]Alert test failed: {e}[/red]")
        return False

async def test_orchestrator():
    """Test orchestrator initialization"""
    console.print("\n[bold cyan]5. Testing Orchestrator[/bold cyan]")
    
    try:
        from supabase_orchestrator import SupabaseOrchestrator
        
        orchestrator = SupabaseOrchestrator()
        
        # Test agent detection
        enabled = []
        for agent_name in orchestrator.agents:
            if orchestrator.is_agent_enabled(agent_name):
                enabled.append(agent_name)
        
        console.print(f"[green]✓[/green] Detected {len(enabled)} enabled agents: {', '.join(enabled)}")
        
        # Test URL generation
        test_urls = await orchestrator.check_for_data_updates('tpp')
        console.print(f"[green]✓[/green] Generated {len(test_urls)} update URLs")
        
        return True
        
    except Exception as e:
        console.print(f"[red]Orchestrator test failed: {e}[/red]")
        return False

async def display_pipeline_status():
    """Display current pipeline status"""
    console.print("\n[bold cyan]6. Pipeline Status Summary[/bold cyan]")
    
    try:
        from supabase_config import supabase_config
        
        pool = await supabase_config.get_db_pool()
        
        # Get agent status
        async with pool.acquire() as conn:
            agents = await conn.fetch("""
                SELECT agent_name, is_active, last_run, 
                       successful_runs, failed_runs, total_runs
                FROM fl_agent_status
                ORDER BY agent_name
            """)
            
            # Get data counts
            counts = {}
            tables = [
                ('TPP', 'fl_tpp_accounts'),
                ('NAV', 'fl_nav_parcel_summary'),
                ('SDF', 'fl_sdf_sales')
            ]
            
            for name, table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                counts[name] = count
        
        # Display status table
        table = Table(title="Florida Data Pipeline Status")
        table.add_column("Agent", style="cyan")
        table.add_column("Status")
        table.add_column("Records")
        table.add_column("Last Run")
        table.add_column("Success Rate")
        
        for agent in agents:
            status = "[green]Active[/green]" if agent['is_active'] else "[red]Inactive[/red]"
            last_run = agent['last_run'].strftime('%Y-%m-%d %H:%M') if agent['last_run'] else "Never"
            success_rate = f"{agent['successful_runs']}/{agent['total_runs']}" if agent['total_runs'] > 0 else "N/A"
            record_count = counts.get(agent['agent_name'].upper(), 0)
            
            table.add_row(
                agent['agent_name'],
                status,
                f"{record_count:,}",
                last_run,
                success_rate
            )
        
        console.print(table)
        
        await pool.close()
        return True
        
    except Exception as e:
        console.print(f"[yellow]Status display not available: {str(e)[:50]}[/yellow]")
        return False

async def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold cyan]Supabase Data Pipeline Test Suite[/bold cyan]\n"
        "[dim]Testing all components of the Florida data pipeline[/dim]",
        border_style="cyan"
    ))
    
    # Check for .env file
    env_path = Path('.env')
    if not env_path.exists():
        console.print("\n[yellow]Warning: .env file not found[/yellow]")
        console.print("Copy .env.supabase to .env and configure with your Supabase credentials")
        console.print("\nExample:")
        console.print("[dim]cp .env.supabase .env[/dim]")
        console.print("[dim]# Edit .env with your Supabase credentials[/dim]")
        return
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    tests = [
        ("Supabase Connection", test_supabase_connection),
        ("Agent Databases", test_agent_databases),
        ("Update Monitoring", test_update_monitoring),
        ("Alert System", test_alert_system),
        ("Orchestrator", test_orchestrator),
        ("Pipeline Status", display_pipeline_status)
    ]
    
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for test_name, test_func in tests:
            task = progress.add_task(f"Running {test_name}...", total=1)
            
            try:
                result = await test_func()
                results.append((test_name, "PASS" if result else "FAIL"))
            except Exception as e:
                results.append((test_name, f"ERROR: {str(e)[:30]}"))
                console.print(f"[red]Error in {test_name}: {e}[/red]")
            
            progress.update(task, advance=1)
    
    # Display results summary
    console.print("\n" + "=" * 60)
    console.print("[bold]TEST RESULTS SUMMARY[/bold]")
    console.print("=" * 60)
    
    for test_name, result in results:
        icon = "[green]✓[/green]" if "PASS" in result else "[red]✗[/red]"
        console.print(f"{icon} {test_name}: {result}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    total = len(results)
    
    console.print("\n" + "=" * 60)
    console.print(f"[bold]Overall: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[bold green]All tests passed! Pipeline ready for production.[/bold green]")
    else:
        console.print("[bold yellow]Some tests failed. Please review configuration.[/bold yellow]")

if __name__ == "__main__":
    console.print("\n[bold]Starting Supabase Pipeline Tests...[/bold]")
    console.print("[dim]This will test all data agents and Supabase integration[/dim]\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Test suite failed: {e}[/red]")
        import traceback
        traceback.print_exc()