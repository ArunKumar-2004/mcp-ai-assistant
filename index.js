#!/usr/bin/env node
const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const serverPath = path.join(__dirname, 'server.py');
const pyprojectPath = path.join(__dirname, 'pyproject.toml');
const installFlagPath = path.join(__dirname, '.deps_installed');

// 1. Determine Python command
const python = process.platform === 'win32' ? 'python' : 'python3';
const pip = process.platform === 'win32' ? 'pip' : 'pip3';

// Check and install dependencies if needed
if (!fs.existsSync(installFlagPath)) {
    try {
        // Install package in editable mode to get all dependencies
        execSync(`${pip} install -e "${__dirname}"`, {
            stdio: 'inherit',
            shell: true
        });
        
        // Create flag file to skip this check next time
        fs.writeFileSync(installFlagPath, new Date().toISOString());
    } catch (err) {
        console.error('⚠️  Warning: Failed to install dependencies automatically.');
        console.error('Please run manually: pip install -e .');
        // Continue anyway - dependencies might already be installed
    }
}

// 3. Spawn the process
const proc = spawn(python, [serverPath, ...process.argv.slice(2)], {
    stdio: ['inherit', 'inherit', 'inherit'],
    shell: process.platform === 'win32'
});

proc.on('error', (err) => {
    if (err.code === 'ENOENT') {
        console.error(`\nERROR: Python not found!`);
        console.error(`Please ensure Python is installed and added to your PATH.`);
        if (process.platform === 'win32') {
            console.error(`TIP: Search for "App Execution Aliases" in Windows settings and turn OFF "Python".`);
        }
    } else {
        console.error(`Failed to start server: ${err.message}`);
    }
    process.exit(1);
});

proc.on('close', (code) => {
    process.exit(code || 0);
});
