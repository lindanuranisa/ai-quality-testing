const { defineConfig } = require("cypress");
const fs = require('fs');
const path = require('path');

module.exports = defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      // Download file handling tasks
      on('task', {
        // Task to clear downloads folder
        clearDownloads() {
          const downloadsPath = path.join(config.downloadsFolder);
          if (fs.existsSync(downloadsPath)) {
            const files = fs.readdirSync(downloadsPath);
            files.forEach(file => {
              const filePath = path.join(downloadsPath, file);
              if (fs.statSync(filePath).isFile()) {
                fs.unlinkSync(filePath);
              }
            });
          }
          return null;
        },

        // Task to move downloaded file to target location with custom name
        moveDownloadedFile({ companyName, targetFolder }) {
          try {
            const downloadsPath = config.downloadsFolder;
            const targetPath = path.join(process.cwd(), targetFolder);
            
            // Create target folder if it doesn't exist
            if (!fs.existsSync(targetPath)) {
              fs.mkdirSync(targetPath, { recursive: true });
            }

            // Find the most recently downloaded PDF file
            const files = fs.readdirSync(downloadsPath)
              .filter(file => file.toLowerCase().endsWith('.pdf'))
              .map(file => ({
                name: file,
                path: path.join(downloadsPath, file),
                mtime: fs.statSync(path.join(downloadsPath, file)).mtime
              }))
              .sort((a, b) => b.mtime - a.mtime);

            if (files.length === 0) {
              return { success: false, error: 'No PDF file found in downloads' };
            }

            const mostRecentFile = files[0];
            const targetFileName = `${companyName}_Investment_Memo.pdf`;
            const targetFilePath = path.join(targetPath, targetFileName);

            // Move and rename the file
            fs.renameSync(mostRecentFile.path, targetFilePath);

            return { 
              success: true, 
              filename: targetFileName,
              fullPath: targetFilePath 
            };
          } catch (error) {
            return { 
              success: false, 
              error: error.message 
            };
          }
        },

        // Task to update config.json with ai_generated_memo path
        updateConfigWithMemoPath({ companyName }) {
          const configPaths = [
            'cypress/fixtures/config.json',  // Cypress fixtures path
            'config.json'                    // Root directory path
          ];
          
          const results = [];
          
          configPaths.forEach(configPath => {
            try {
              const fullConfigPath = path.join(process.cwd(), configPath);
              
              // Check if file exists
              if (!fs.existsSync(fullConfigPath)) {
                results.push({
                  path: configPath,
                  success: false,
                  error: `File does not exist: ${configPath}`
                });
                return;
              }
              
              // Read current config
              const configData = JSON.parse(fs.readFileSync(fullConfigPath, 'utf8'));
              
              // Find the company and update ai_generated_memo path
              const company = configData.companies.find(c => c.name === companyName);
              if (company) {
                company.ai_generated_memo = `data/ai_outputs/${companyName}_Investment_Memo.pdf`;
                
                // Write updated config back to file
                fs.writeFileSync(fullConfigPath, JSON.stringify(configData, null, 2));
                
                results.push({
                  path: configPath,
                  success: true,
                  message: `Updated ${configPath} with memo path for ${companyName}`,
                  memoPath: company.ai_generated_memo
                });
              } else {
                results.push({
                  path: configPath,
                  success: false,
                  error: `Company ${companyName} not found in ${configPath}`
                });
              }
            } catch (error) {
              results.push({
                path: configPath,
                success: false,
                error: `Error updating ${configPath}: ${error.message}`
              });
            }
          });
          
          const successCount = results.filter(r => r.success).length;
          
          return {
            success: successCount > 0,
            totalFiles: configPaths.length,
            successCount: successCount,
            results: results,
            summary: `Updated ${successCount}/${configPaths.length} config files for ${companyName}`
          };
        }
      });
    },
    baseUrl: "https://alphame.adgo.dev/",
    specPattern: 'cypress/e2e/**/*.{js,jsx,ts,tsx}',
    downloadsFolder: 'cypress/downloads', // Add downloads folder configuration
  },
  env: {
    apiKey: process.env.API_TOKEN,
    accessToken: process.env.ACCESS_TOKEN,
  }
});