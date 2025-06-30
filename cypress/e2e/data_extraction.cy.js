Cypress.on('uncaught:exception', (err, runnable) => {
    if (err.message.includes('Clipboard')) {
        return false;
    }
    return true;
});

describe('Frontend Data Extraction - AI Output Verification', () => {
    beforeEach(() => {
        cy.viewport(1440, 900);
        cy.session('user-login', () => {
            cy.visit('/');
            cy.loginByGoogleApi();
        });
    });

    it('Extract AI-generated frontend data for quality verification', () => {
        // Load config.json (matches our corrected strategy)
        cy.fixture('config.json').then((config) => {
            const companies = config.companies;
            cy.log(`📊 Starting AI Output extraction for ${companies.length} companies`);
            cy.log(`🎯 Strategy: Extracting AI-generated frontend data to verify against source files`);
            
            // Process companies one by one using cy.wrap().each()
            cy.wrap(companies).each((company, index) => {
                cy.log(`🏢 Processing company ${index + 1}/${companies.length}: ${company.name}`);
                
                // Initialize verification records structure (AI Output 1)
                const verifyRecords = {
                    "company_name": "",
                    "industry": "",
                    "location": "",
                    "founders": "",
                    "founder_email": "",
                    "year_founded": "",
                    "funding_stage": "",
                    "latest_valuation": "",
                    "fund_raise_target": "",
                    "amount_raised": "",
                    "revenue": "",
                    "list_of_investors": "",
                    "lead_investor": "",
                    "verticals": "",
                    "keywords": "",
                    // Add metadata for our strategy
                    "_extraction_metadata": {
                        "extracted_at": new Date().toISOString(),
                        "company_id": company.id,
                        "frontend_url": company.frontend_url,
                        "extraction_type": "ai_output_verification",
                        "total_fields": 15
                    }
                };

                // Visit company page
                cy.visit(company.frontend_url);
                cy.wait(3000);
                cy.url().should('include', 'company-detail'); // Verify we're on the right page

                // Extract all fields for this company using your working logic
                cy.extractCompanyFields(verifyRecords);

                // Save results in the format expected by our Python scripts
                cy.then(() => {
                    // Filename format: {company_name}_frontend_data.json (matches main.py expectation)
                    const filename = `data/extracted/${company.name}_frontend_data.json`;
                    
                    // Add summary to the data
                    const fieldsWithData = Object.keys(verifyRecords).filter(key => 
                        !key.startsWith('_') && verifyRecords[key] && verifyRecords[key].toString().trim() !== ''
                    ).length;
                    
                    verifyRecords._extraction_metadata.fields_extracted = fieldsWithData;
                    verifyRecords._extraction_metadata.extraction_success = fieldsWithData > 0;
                    
                    cy.writeFile(filename, JSON.stringify(verifyRecords, null, 2));
                    cy.log(`✅ AI Output extracted for ${company.name}: ${fieldsWithData}/15 fields`);
                    cy.log(`📄 Saved to: ${filename}`);
                });
            });

            // Summary after all companies
            cy.then(() => {
                cy.log(`🎉 AI Output extraction completed for all ${companies.length} companies!`);
                cy.log(`📋 Next: Run Python script to verify AI outputs against source files`);
                cy.log(`🚀 Command: python python/src/main.py`);
            });
        });
    });
});
