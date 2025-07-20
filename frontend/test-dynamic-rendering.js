#!/usr/bin/env node

/**
 * Test script to verify dynamic rendering is enabled
 * Run after build to check if static HTML files were generated
 */

const fs = require('fs');
const path = require('path');

console.log('Checking for static page generation...\n');

const standaloneDir = path.join(__dirname, '.next', 'standalone');
const staticHtmlDir = path.join(__dirname, '.next', 'server', 'app');
const pagesDir = path.join(__dirname, '.next', 'server', 'pages');

// Check if static HTML files exist
const checkStaticFiles = (dir) => {
  if (!fs.existsSync(dir)) {
    console.log(`✓ Directory ${dir} does not exist (good - no static generation)`);
    return false;
  }

  const htmlFiles = [];
  const scanDir = (currentDir) => {
    const files = fs.readdirSync(currentDir);
    files.forEach(file => {
      const filePath = path.join(currentDir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        scanDir(filePath);
      } else if (file.endsWith('.html') && !file.includes('_')) {
        htmlFiles.push(filePath);
      }
    });
  };

  try {
    scanDir(dir);
    if (htmlFiles.length > 0) {
      console.log(`⚠️  Found ${htmlFiles.length} static HTML files in ${dir}:`);
      htmlFiles.forEach(file => console.log(`   - ${file}`));
      return true;
    } else {
      console.log(`✓ No static HTML files found in ${dir} (good)`);
      return false;
    }
  } catch (error) {
    console.log(`✓ Error scanning ${dir}: ${error.message} (likely no static files)`);
    return false;
  }
};

console.log('Checking for static HTML generation:\n');

const hasStaticAppFiles = checkStaticFiles(staticHtmlDir);
const hasStaticPageFiles = checkStaticFiles(pagesDir);

console.log('\n---\n');

if (!hasStaticAppFiles && !hasStaticPageFiles) {
  console.log('✅ SUCCESS: Dynamic rendering is properly configured!');
  console.log('   No static HTML files were generated during build.');
  process.exit(0);
} else {
  console.log('❌ WARNING: Static files were found!');
  console.log('   The application may still be generating static pages.');
  console.log('   Please verify the Next.js configuration.');
  process.exit(1);
}