#!/bin/bash

# ConcordBroker Initial Setup Script

set -e

echo "🏗️ ConcordBroker Setup Script"
echo "=============================="

# Check system requirements
check_requirements() {
    echo "📋 Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed"
        echo "Please install Docker from https://docker.com"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not installed"
        echo "Please install Node.js from https://nodejs.org"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed"
        echo "Please install Python 3.11+"
        exit 1
    fi
    
    echo "✅ All requirements met"
}

# Setup environment variables
setup_env() {
    echo "🔧 Setting up environment variables..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "Created .env file from template"
        echo "Please edit .env and add your credentials"
    else
        echo ".env file already exists"
    fi
}

# Install dependencies
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    # Backend dependencies
    echo "Installing backend dependencies..."
    cd apps/api
    pip install -r requirements.txt
    cd ../..
    
    # Frontend dependencies
    echo "Installing frontend dependencies..."
    cd apps/web
    npm install
    cd ../..
    
    # Worker dependencies
    for worker in sunbiz_loader bcpa_scraper official_records dor_processor; do
        echo "Installing $worker dependencies..."
        cd apps/workers/$worker
        pip install -r requirements.txt
        cd ../../..
    done
    
    echo "✅ All dependencies installed"
}

# Setup database
setup_database() {
    echo "🗄️ Setting up database..."
    
    # Start PostgreSQL container
    docker-compose up -d postgres
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 10
    
    # Create initial schema
    docker-compose exec postgres psql -U concordbroker -c "
        CREATE SCHEMA IF NOT EXISTS public;
        GRANT ALL ON SCHEMA public TO concordbroker;
    "
    
    echo "✅ Database setup complete"
}

# Initialize services
initialize_services() {
    echo "🚀 Initializing services..."
    
    # Build Docker images
    docker-compose build
    
    # Start all services
    docker-compose up -d
    
    echo "✅ Services initialized"
}

# Create initial admin user
create_admin() {
    echo "👤 Creating admin user..."
    
    read -p "Enter admin phone number (10 digits): " phone
    
    # Store admin phone in database
    docker-compose exec api python -c "
import asyncio
from database import Database

async def create_admin():
    db = Database()
    await db.connect()
    await db.execute(
        'INSERT INTO admin_users (phone) VALUES (\$1)',
        '+1$phone'
    )
    await db.disconnect()
    print('Admin user created')

asyncio.run(create_admin())
"
}

# Main setup flow
main() {
    echo ""
    echo "This script will set up ConcordBroker on your system"
    echo ""
    
    check_requirements
    setup_env
    
    read -p "Do you want to install all dependencies? (y/n): " install
    if [ "$install" = "y" ]; then
        install_dependencies
    fi
    
    read -p "Do you want to set up the database? (y/n): " database
    if [ "$database" = "y" ]; then
        setup_database
    fi
    
    read -p "Do you want to start all services? (y/n): " services
    if [ "$services" = "y" ]; then
        initialize_services
    fi
    
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your credentials"
    echo "2. Run 'make up' to start services"
    echo "3. Visit http://localhost:5173 for the web interface"
    echo "4. Visit http://localhost:8000/docs for API documentation"
    echo ""
}

# Run main function
main