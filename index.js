#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const serverPath = path.join(__dirname, 'server.py');
const requirementsPath = path.join(__dirname, 'requirements.txt');

// 1. Determine Python command
const python = process.platform === 'win32' ? 'python' : 'python3';

console.error(`Starting AI Deployment Readiness Assistant via ${python}...`);

// 2. Spawn the process
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
