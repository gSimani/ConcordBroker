#!/bin/bash

# ConcordBroker Deployment Script

set -e

echo "🚀 Starting ConcordBroker deployment..."

# Check if required environment variables are set
check_env() {
    if [ -z "$1" ]; then
        echo "❌ Error: $2 is not set"
        exit 1
    fi
}

# Deploy to Railway
deploy_railway() {
    echo "📦 Deploying backend to Railway..."
    
    # Check Railway CLI is installed
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    # Login to Railway
    railway login
    
    # Link project (if not already linked)
    railway link
    
    # Deploy backend services
    railway up
    
    echo "✅ Backend deployed to Railway"
}

# Deploy to Vercel
deploy_vercel() {
    echo "📦 Deploying frontend to Vercel..."
    
    cd apps/web
    
    # Check Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        echo "Installing Vercel CLI..."
        npm install -g vercel
    fi
    
    # Build the frontend
    npm run build
    
    # Deploy to Vercel
    vercel --prod
    
    cd ../..
    
    echo "✅ Frontend deployed to Vercel"
}

# Run database migrations
run_migrations() {
    echo "🗄️ Running database migrations..."
    
    # Get database URL from Railway
    DATABASE_URL=$(railway vars get DATABASE_URL)
    
    if [ -z "$DATABASE_URL" ]; then
        echo "❌ Could not get DATABASE_URL from Railway"
        exit 1
    fi
    
    # Run migrations
    docker run --rm \
        -e DATABASE_URL="$DATABASE_URL" \
        concordbroker-api \
        python -m alembic upgrade head
        
    echo "✅ Migrations complete"
}

# Main deployment flow
main() {
    echo "Which environment do you want to deploy to?"
    echo "1) Production"
    echo "2) Staging"
    read -p "Enter choice [1-2]: " choice
    
    case $choice in
        1)
            echo "Deploying to PRODUCTION..."
            
            # Confirm production deployment
            read -p "⚠️  Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                echo "Deployment cancelled"
                exit 0
            fi
            
            # Deploy backend
            deploy_railway
            
            # Run migrations
            run_migrations
            
            # Deploy frontend
            deploy_vercel
            
            echo "🎉 Production deployment complete!"
            ;;
            
        2)
            echo "Deploying to STAGING..."
            
            # Deploy with staging configuration
            railway up --environment staging
            vercel --env preview
            
            echo "🎉 Staging deployment complete!"
            ;;
            
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
}

# Run main function
main