/**
 * ConcordBroker NPM Dependency Monitor
 * Monitors critical Node.js/npm dependencies for updates
 * Companion to the Python dependency monitor
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const axios = require('axios');

class NpmDependencyMonitor {
    constructor() {
        this.projectRoot = path.join(__dirname, '..', '..');
        this.mcpUrl = 'http://localhost:3001';
        this.mcpApiKey = 'concordbroker-mcp-key';

        // Critical npm packages for ConcordBroker
        this.monitoredPackages = {
            // Frontend (React/Vite)
            'react': {
                releaseNotes: 'https://github.com/facebook/react/releases',
                npmUrl: 'https://www.npmjs.com/package/react',
                critical: true,
                description: 'React library'
            },
            'react-dom': {
                releaseNotes: 'https://github.com/facebook/react/releases',
                npmUrl: 'https://www.npmjs.com/package/react-dom',
                critical: true,
                description: 'React DOM bindings'
            },
            'vite': {
                releaseNotes: 'https://github.com/vitejs/vite/releases',
                npmUrl: 'https://www.npmjs.com/package/vite',
                critical: true,
                description: 'Frontend build tool'
            },
            'typescript': {
                releaseNotes: 'https://github.com/microsoft/TypeScript/releases',
                npmUrl: 'https://www.npmjs.com/package/typescript',
                critical: true,
                description: 'TypeScript compiler'
            },

            // API/Backend
            'fastify': {
                releaseNotes: 'https://github.com/fastify/fastify/releases',
                npmUrl: 'https://www.npmjs.com/package/fastify',
                critical: true,
                description: 'Fast web framework'
            },
            'express': {
                releaseNotes: 'https://github.com/expressjs/express/releases',
                npmUrl: 'https://www.npmjs.com/package/express',
                critical: true,
                description: 'Web framework'
            },

            // Database/Storage
            '@supabase/supabase-js': {
                releaseNotes: 'https://github.com/supabase/supabase-js/releases',
                npmUrl: 'https://www.npmjs.com/package/@supabase/supabase-js',
                critical: true,
                description: 'Supabase client'
            },

            // Development Tools
            'eslint': {
                releaseNotes: 'https://github.com/eslint/eslint/releases',
                npmUrl: 'https://www.npmjs.com/package/eslint',
                critical: false,
                description: 'JavaScript linter'
            },
            'prettier': {
                releaseNotes: 'https://github.com/prettier/prettier/releases',
                npmUrl: 'https://www.npmjs.com/package/prettier',
                critical: false,
                description: 'Code formatter'
            },

            // Testing
            'vitest': {
                releaseNotes: 'https://github.com/vitest-dev/vitest/releases',
                npmUrl: 'https://www.npmjs.com/package/vitest',
                critical: false,
                description: 'Testing framework'
            },
            'jest': {
                releaseNotes: 'https://github.com/facebook/jest/releases',
                npmUrl: 'https://www.npmjs.com/package/jest',
                critical: false,
                description: 'Testing framework'
            },

            // Utility Libraries
            'lodash': {
                releaseNotes: 'https://github.com/lodash/lodash/releases',
                npmUrl: 'https://www.npmjs.com/package/lodash',
                critical: false,
                description: 'Utility library'
            },
            'axios': {
                releaseNotes: 'https://github.com/axios/axios/releases',
                npmUrl: 'https://www.npmjs.com/package/axios',
                critical: true,
                description: 'HTTP client'
            },

            // UI Components
            '@radix-ui/react-dialog': {
                releaseNotes: 'https://github.com/radix-ui/primitives/releases',
                npmUrl: 'https://www.npmjs.com/package/@radix-ui/react-dialog',
                critical: false,
                description: 'UI components'
            },
            'tailwindcss': {
                releaseNotes: 'https://github.com/tailwindlabs/tailwindcss/releases',
                npmUrl: 'https://www.npmjs.com/package/tailwindcss',
                critical: false,
                description: 'CSS framework'
            }
        };

        this.reportFile = path.join(this.projectRoot, 'npm_dependency_report.json');
        this.lastCheckFile = path.join(this.projectRoot, 'npm_dependency_last_check.json');
    }

    async checkAllDependencies() {
        console.log('🔍 Starting npm dependency update check...');

        // Find all package.json files
        const packageJsonFiles = await this.findPackageJsonFiles();

        const results = {
            timestamp: new Date().toISOString(),
            projects: {},
            summary: {
                totalProjects: packageJsonFiles.length,
                totalPackages: 0,
                updatesAvailable: 0,
                criticalUpdates: 0,
                errors: 0
            }
        };

        for (const packageJsonFile of packageJsonFiles) {
            try {
                const projectPath = path.dirname(packageJsonFile);
                const projectName = path.basename(projectPath);

                console.log(`Checking project: ${projectName}`);

                const packageJson = JSON.parse(fs.readFileSync(packageJsonFile, 'utf8'));
                const outdatedPackages = await this.getOutdatedPackages(projectPath);

                const projectResults = {
                    path: projectPath,
                    packages: {},
                    summary: {
                        totalChecked: 0,
                        updatesAvailable: 0,
                        criticalUpdates: 0
                    }
                };

                // Check dependencies and devDependencies
                const allDeps = {
                    ...packageJson.dependencies || {},
                    ...packageJson.devDependencies || {}
                };

                for (const [packageName, currentVersion] of Object.entries(allDeps)) {
                    if (this.monitoredPackages[packageName]) {
                        const outdatedInfo = outdatedPackages[packageName];
                        const latestVersion = outdatedInfo ? outdatedInfo.latest : currentVersion;
                        const hasUpdate = outdatedInfo && outdatedInfo.current !== outdatedInfo.latest;

                        projectResults.packages[packageName] = {
                            currentVersion: currentVersion.replace(/[^0-9.]/g, ''),
                            latestVersion: latestVersion,
                            hasUpdate: hasUpdate,
                            isCritical: this.monitoredPackages[packageName].critical,
                            description: this.monitoredPackages[packageName].description,
                            releaseNotesUrl: this.monitoredPackages[packageName].releaseNotes,
                            npmUrl: this.monitoredPackages[packageName].npmUrl,
                            updateCommand: `npm install ${packageName}@latest`,
                            lastChecked: new Date().toISOString()
                        };

                        projectResults.summary.totalChecked++;
                        if (hasUpdate) {
                            projectResults.summary.updatesAvailable++;
                            if (this.monitoredPackages[packageName].critical) {
                                projectResults.summary.criticalUpdates++;
                            }
                        }
                    }
                }

                results.projects[projectName] = projectResults;
                results.summary.totalPackages += projectResults.summary.totalChecked;
                results.summary.updatesAvailable += projectResults.summary.updatesAvailable;
                results.summary.criticalUpdates += projectResults.summary.criticalUpdates;

            } catch (error) {
                console.error(`Error checking ${packageJsonFile}:`, error.message);
                results.summary.errors++;
            }
        }

        // Save results
        await this.saveReport(results);

        // Notify MCP Server if critical updates available
        if (results.summary.criticalUpdates > 0) {
            await this.notifyMcpServer(results);
        }

        return results;
    }

    async findPackageJsonFiles() {
        const packageJsonFiles = [];

        const searchDirs = [
            path.join(this.projectRoot, 'apps', 'web'),
            path.join(this.projectRoot, 'mcp-server'),
            this.projectRoot
        ];

        for (const dir of searchDirs) {
            const packageJsonPath = path.join(dir, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                packageJsonFiles.push(packageJsonPath);
            }
        }

        return packageJsonFiles;
    }

    async getOutdatedPackages(projectPath) {
        try {
            const result = execSync('npm outdated --json', {
                cwd: projectPath,
                encoding: 'utf8',
                stdio: ['ignore', 'pipe', 'ignore']
            });

            return JSON.parse(result);
        } catch (error) {
            // npm outdated returns exit code 1 when packages are outdated
            if (error.stdout) {
                try {
                    return JSON.parse(error.stdout);
                } catch (parseError) {
                    console.warn(`Could not parse npm outdated output for ${projectPath}`);
                }
            }
            return {};
        }
    }

    async saveReport(results) {
        try {
            fs.writeFileSync(this.reportFile, JSON.stringify(results, null, 2));
            fs.writeFileSync(this.lastCheckFile, JSON.stringify({
                lastCheck: new Date().toISOString()
            }, null, 2));

            console.log(`📝 Report saved to ${this.reportFile}`);
        } catch (error) {
            console.error('Error saving report:', error);
        }
    }

    async notifyMcpServer(results) {
        try {
            const criticalUpdates = [];

            for (const [projectName, projectData] of Object.entries(results.projects)) {
                for (const [packageName, packageInfo] of Object.entries(projectData.packages)) {
                    if (packageInfo.hasUpdate && packageInfo.isCritical) {
                        criticalUpdates.push(`${projectName}/${packageName}`);
                    }
                }
            }

            const notificationData = {
                type: 'npm_dependency_update',
                timestamp: new Date().toISOString(),
                criticalUpdates: criticalUpdates,
                totalUpdates: results.summary.updatesAvailable,
                message: `🚨 ${criticalUpdates.length} critical npm dependency updates available`
            };

            const response = await axios.post(
                `${this.mcpUrl}/api/notifications`,
                notificationData,
                {
                    headers: { 'x-api-key': this.mcpApiKey },
                    timeout: 10000
                }
            );

            if (response.status === 200) {
                console.log('✅ MCP Server notified about critical npm updates');
            } else {
                console.warn(`⚠️ Failed to notify MCP Server: ${response.status}`);
            }

        } catch (error) {
            console.error('Error notifying MCP Server:', error.message);
        }
    }

    async generateUpdateScript() {
        const scriptContent = `@echo off
echo ================================================================
echo  ConcordBroker NPM Dependency Update Script
echo  Auto-generated on ${new Date().toLocaleString()}
echo ================================================================
echo.

echo Checking Node.js and npm...
node --version
npm --version

echo.
echo Updating npm packages...

cd /d "${path.join(this.projectRoot, 'apps', 'web')}"
echo Updating frontend dependencies...
npm update

cd /d "${path.join(this.projectRoot, 'mcp-server')}"
echo Updating MCP server dependencies...
npm update

cd /d "${this.projectRoot}"
echo Updating root dependencies...
npm update

echo.
echo ================================================================
echo  NPM Update Complete! Checking for audit issues...
echo ================================================================

cd /d "${path.join(this.projectRoot, 'apps', 'web')}"
npm audit

cd /d "${path.join(this.projectRoot, 'mcp-server')}"
npm audit

echo.
echo NPM update script completed!
pause
`;

        const scriptPath = path.join(this.projectRoot, 'update_npm_dependencies.bat');
        fs.writeFileSync(scriptPath, scriptContent);

        console.log(`📝 NPM update script saved to ${scriptPath}`);
        return scriptPath;
    }
}

async function main() {
    const monitor = new NpmDependencyMonitor();

    try {
        // Check all dependencies
        const results = await monitor.checkAllDependencies();

        // Print summary
        const summary = results.summary;
        console.log(`\n📊 NPM Dependency Check Summary:`);
        console.log(`   Projects checked: ${summary.totalProjects}`);
        console.log(`   Total packages checked: ${summary.totalPackages}`);
        console.log(`   Updates available: ${summary.updatesAvailable}`);
        console.log(`   Critical updates: ${summary.criticalUpdates}`);
        console.log(`   Errors: ${summary.errors}`);

        // Show projects with updates
        if (summary.updatesAvailable > 0) {
            console.log(`\n🔄 Projects with updates available:`);
            for (const [projectName, projectData] of Object.entries(results.projects)) {
                if (projectData.summary.updatesAvailable > 0) {
                    console.log(`   📦 ${projectName}: ${projectData.summary.updatesAvailable} updates (${projectData.summary.criticalUpdates} critical)`);
                }
            }
        }

        // Generate update script
        const scriptPath = await monitor.generateUpdateScript();
        console.log(`\n📝 Update script generated: ${scriptPath}`);

        return results;

    } catch (error) {
        console.error('Error in dependency monitoring:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = NpmDependencyMonitor;